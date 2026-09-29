from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from watermark_project.config import GenerationProtocolConfig
from watermark_project.edits import EditEvent
from watermark_project.modeling import (
    BaseLanguageModel,
    apply_repetition_penalty,
    build_ascii_token_ban_mask,
    render_prompt_for_model,
    sample_token_from_logits,
    stable_hash_int,
)


PATTERNS: Dict[str, Tuple[int, ...]] = {
    "AB": (0, 1),
    "ACADBCBD": (0, 2, 0, 3, 1, 2, 1, 3),
}

_MASK64 = (1 << 64) - 1
_MIX_A = 0x9E3779B97F4A7C15
_MIX_B = 0xBF58476D1CE4E5B9
_MIX_C = 0x94D049BB133111EB


def resolve_pattern(name: str) -> Tuple[int, ...]:
    normalized = name.strip().upper()
    try:
        return PATTERNS[normalized]
    except KeyError as exc:
        raise ValueError(
            f"Unknown combinatorial pattern {name!r}; choose from {sorted(PATTERNS)}."
        ) from exc


def _mix64_scalar(value: int) -> int:
    value = (int(value) + _MIX_A) & _MASK64
    value = ((value ^ (value >> 30)) * _MIX_B) & _MASK64
    value = ((value ^ (value >> 27)) * _MIX_C) & _MASK64
    return (value ^ (value >> 31)) & _MASK64


def _context_seed(previous_token_id: int, key: int) -> int:
    return _mix64_scalar(
        (int(key) & _MASK64)
        ^ _mix64_scalar(int(previous_token_id) & _MASK64)
    )


def context_token_color(
    token_id: int,
    previous_token_id: int,
    key: int,
    num_colors: int,
) -> int:
    """Assign one token to a context-dependent pseudorandom color."""
    if num_colors <= 0:
        raise ValueError("num_colors must be positive.")
    mixed = _mix64_scalar((int(token_id) & _MASK64) ^ _context_seed(previous_token_id, key))
    return int(mixed % int(num_colors))


def context_color_vector(
    vocab_size: int,
    previous_token_id: int,
    key: int,
    num_colors: int,
) -> np.ndarray:
    """Assign every vocabulary item to exactly one context-dependent color."""
    if vocab_size <= 0:
        raise ValueError("vocab_size must be positive.")
    if num_colors <= 0:
        raise ValueError("num_colors must be positive.")
    seed = np.uint64(_context_seed(previous_token_id, key))
    values = np.arange(vocab_size, dtype=np.uint64) ^ seed
    with np.errstate(over="ignore"):
        values = values + np.uint64(_MIX_A)
        values = (values ^ (values >> np.uint64(30))) * np.uint64(_MIX_B)
        values = (values ^ (values >> np.uint64(27))) * np.uint64(_MIX_C)
        values = values ^ (values >> np.uint64(31))
    return (values % np.uint64(num_colors)).astype(np.int16)


@dataclass(frozen=True)
class CombinatorialConfig:
    pattern_name: str = "ACADBCBD"
    watermark_key: int = 3779
    window_size: Optional[int] = None
    evaluation_block_len: int = 8
    target_clean_far: float = 0.1

    @property
    def pattern(self) -> Tuple[int, ...]:
        return resolve_pattern(self.pattern_name)

    @property
    def num_colors(self) -> int:
        return max(self.pattern) + 1

    @property
    def resolved_window_size(self) -> int:
        return int(self.window_size or len(self.pattern))

    def __post_init__(self) -> None:
        if self.evaluation_block_len <= 0:
            raise ValueError("evaluation_block_len must be positive.")
        if self.window_size is not None and self.window_size <= 0:
            raise ValueError("window_size must be positive.")
        if not 0.0 <= self.target_clean_far < 1.0:
            raise ValueError("target_clean_far must be in [0, 1).")
        resolve_pattern(self.pattern_name)


@dataclass
class CombinatorialGenerationResult:
    prompt: str
    user_prompt: str
    rendered_prompt: str
    prompt_mode: str
    prompt_token_ids: List[int]
    suffix_text: str
    full_text: str
    generated_token_ids: List[int]
    generated_colors: List[int]
    target_colors: List[int]
    block_tokens: List[List[int]]
    pattern_adherence: float
    raw_top_trace: List[Dict[str, Any]]


class CombinatorialWatermark:
    """Independent implementation of the pattern-based prior work."""

    def __init__(
        self,
        model: BaseLanguageModel,
        config: CombinatorialConfig,
        protocol: GenerationProtocolConfig,
    ):
        self.model = model
        self.config = config
        self.protocol = protocol
        self.ban_mask = build_ascii_token_ban_mask(model, protocol.ascii_token_filter)
        for token_id in model.all_special_ids:
            if 0 <= int(token_id) < len(self.ban_mask):
                self.ban_mask[int(token_id)] = True

    def generate_one(
        self,
        prompt: str,
        *,
        logit_bias: float,
        target_blocks: int,
        max_new_tokens: int,
        seed: int,
    ) -> CombinatorialGenerationResult:
        target_tokens = int(target_blocks) * int(self.config.evaluation_block_len)
        if max_new_tokens < target_tokens:
            raise ValueError(
                f"max_new_tokens={max_new_tokens} cannot produce "
                f"{target_blocks} x {self.config.evaluation_block_len}={target_tokens} tokens."
            )
        user_prompt, rendered_prompt, prompt_mode = render_prompt_for_model(
            self.model,
            prompt,
            self.protocol,
        )
        session = self.model.start_session(
            rendered_prompt,
            add_special_tokens=prompt_mode != "chat_template",
            clean=prompt_mode != "chat_template",
        )
        if not session.prompt_ids:
            raise RuntimeError("The rendered prompt produced no token ids.")
        rng = np.random.default_rng(
            (int(seed) + stable_hash_int(rendered_prompt)) % (2**32)
        )
        generated_ids: List[int] = []
        generated_colors: List[int] = []
        target_colors: List[int] = []
        raw_top_trace: List[Dict[str, Any]] = []
        pattern = self.config.pattern

        for step in range(target_tokens):
            raw_logits = np.asarray(session.next_logits(), dtype=np.float64)
            adjusted = apply_repetition_penalty(
                raw_logits,
                generated_ids,
                self.protocol.repetition_penalty,
            )
            adjusted[self.ban_mask] = -1e9
            previous_token_id = (
                generated_ids[-1] if generated_ids else int(session.prompt_ids[-1])
            )
            colors = context_color_vector(
                self.model.vocab_size,
                previous_token_id,
                self.config.watermark_key,
                self.config.num_colors,
            )
            target_color = int(pattern[step % len(pattern)])
            adjusted = adjusted + float(logit_bias) * (colors == target_color)
            next_id = sample_token_from_logits(adjusted, rng, self.protocol)
            chosen_color = int(colors[next_id])
            raw_top_trace.append(
                {
                    "step": int(step),
                    "previous_token_id": int(previous_token_id),
                    "raw_top_id": int(np.argmax(raw_logits)),
                    "chosen_id": int(next_id),
                    "chosen_color": chosen_color,
                    "target_color": target_color,
                }
            )
            session.append(next_id)
            generated_ids.append(int(next_id))
            generated_colors.append(chosen_color)
            target_colors.append(target_color)

        block_len = self.config.evaluation_block_len
        block_tokens = [
            generated_ids[start : start + block_len]
            for start in range(0, len(generated_ids), block_len)
        ]
        adherence = float(
            np.mean(np.asarray(generated_colors) == np.asarray(target_colors))
        )
        return CombinatorialGenerationResult(
            prompt=prompt,
            user_prompt=user_prompt,
            rendered_prompt=rendered_prompt,
            prompt_mode=prompt_mode,
            prompt_token_ids=[int(x) for x in session.prompt_ids],
            suffix_text=self.model.decode(generated_ids, skip_special_tokens=True),
            full_text=self.model.decode(
                list(session.prompt_ids) + generated_ids,
                skip_special_tokens=True,
            ),
            generated_token_ids=generated_ids,
            generated_colors=generated_colors,
            target_colors=target_colors,
            block_tokens=block_tokens,
            pattern_adherence=adherence,
            raw_top_trace=raw_top_trace,
        )

    def token_colors(
        self,
        token_ids: Sequence[int],
        initial_previous_token_id: int,
    ) -> List[int]:
        colors: List[int] = []
        previous = int(initial_previous_token_id)
        for token_id in token_ids:
            color = context_token_color(
                int(token_id),
                previous,
                self.config.watermark_key,
                self.config.num_colors,
            )
            colors.append(color)
            previous = int(token_id)
        return colors

    def score_tokens(
        self,
        token_ids: Sequence[int],
        initial_previous_token_id: int,
    ) -> Dict[str, Any]:
        colors = self.token_colors(token_ids, initial_previous_token_id)
        indicators = cyclic_window_indicators(
            colors,
            self.config.pattern,
            self.config.resolved_window_size,
        )
        local_scores = local_edit_scores(
            len(colors),
            indicators,
            self.config.resolved_window_size,
        )
        return {
            "colors": colors,
            "window_indicators": indicators.tolist(),
            "global_score": float(np.mean(indicators)) if indicators.size else 0.0,
            "local_scores": local_scores.tolist(),
        }


def cyclic_window_indicators(
    colors: Sequence[int],
    pattern: Sequence[int],
    window_size: int,
) -> np.ndarray:
    if window_size <= 0:
        raise ValueError("window_size must be positive.")
    if not pattern:
        raise ValueError("pattern must not be empty.")
    if len(colors) < window_size:
        return np.zeros(0, dtype=np.int8)
    rotations = {
        tuple(pattern[(shift + offset) % len(pattern)] for offset in range(window_size))
        for shift in range(len(pattern))
    }
    return np.asarray(
        [
            int(tuple(int(x) for x in colors[start : start + window_size]) in rotations)
            for start in range(len(colors) - window_size + 1)
        ],
        dtype=np.int8,
    )


def local_edit_scores(
    token_count: int,
    window_indicators: Sequence[int],
    window_size: int,
) -> np.ndarray:
    """Source-faithful edge handling: nonexistent edge windows count as matches."""
    indicators = np.asarray(window_indicators, dtype=np.float64)
    scores = np.ones(int(token_count), dtype=np.float64)
    for token_index in range(int(token_count)):
        matches = 0.0
        for offset in range(-window_size + 1, 1):
            start = token_index + offset
            if 0 <= start < indicators.size:
                matches += float(indicators[start])
            else:
                matches += 1.0
        scores[token_index] = matches / float(window_size)
    return scores


def calibrate_lower_tail_threshold(
    clean_scores: Sequence[float],
    target_far: float,
) -> float:
    """Legacy inclusive threshold used by the earlier block-calibrated runner."""
    scores = np.asarray(list(clean_scores), dtype=np.float64)
    if scores.size == 0:
        raise ValueError("Cannot calibrate a threshold from no scores.")
    candidates = np.unique(scores)
    valid = [
        float(candidate)
        for candidate in candidates
        if float(np.mean(scores <= candidate)) <= float(target_far) + 1e-12
    ]
    if valid:
        return max(valid)
    return float(np.nextafter(np.min(scores), -np.inf))


def calibrate_strict_lower_tail_threshold(
    clean_scores: Sequence[float],
    target_far: float,
) -> float:
    """Largest observed tau with empirical Pr[score < tau] at most target."""
    scores = np.asarray(list(clean_scores), dtype=np.float64)
    if scores.size == 0:
        raise ValueError("Cannot calibrate a threshold from no scores.")
    candidates = np.unique(scores)
    valid = [
        float(candidate)
        for candidate in candidates
        if float(np.mean(scores < candidate)) <= float(target_far) + 1e-12
    ]
    if not valid:
        raise RuntimeError("The minimum observed score must define a valid threshold.")
    return max(valid)


def complete_mismatch_threshold(pattern_name: str) -> float:
    """Threshold that flags a local window only when none of its checks match."""
    return 1.0 / len(resolve_pattern(pattern_name))


def split_scores_by_blocks(
    scores: Sequence[float],
    blocks: Sequence[Sequence[int]],
) -> List[List[float]]:
    result: List[List[float]] = []
    pointer = 0
    for block in blocks:
        end = pointer + len(block)
        result.append([float(x) for x in scores[pointer:end]])
        pointer = end
    if pointer != len(scores):
        raise ValueError("Block lengths do not cover the score sequence.")
    return result


def clean_block_min_scores(
    local_scores: Sequence[float],
    block_len: int,
) -> List[float]:
    if len(local_scores) % int(block_len) != 0:
        raise ValueError("Clean local score length must be divisible by block_len.")
    return [
        float(np.min(local_scores[start : start + block_len]))
        for start in range(0, len(local_scores), block_len)
    ]


def evaluate_combinatorial_blocks(
    original_blocks: Sequence[Sequence[int]],
    observed_blocks: Sequence[Sequence[int]],
    origin_maps_per_block: Sequence[Sequence[int]],
    gt_events_per_block: Sequence[Sequence[EditEvent]],
    local_scores: Sequence[float],
    *,
    token_threshold: float,
    block_threshold: float | None = None,
    threshold_mode: str = "original_token",
) -> Dict[str, Any]:
    strict_token_modes = {
        "fixed_complete_mismatch",
        "clean_type_i_0.1",
        "original_token",
    }
    if threshold_mode not in strict_token_modes | {"legacy_separate_block"}:
        raise ValueError(f"Unknown threshold mode: {threshold_mode!r}.")
    if threshold_mode == "legacy_separate_block" and block_threshold is None:
        raise ValueError("Legacy mode requires a separately calibrated block threshold.")

    score_blocks = split_scores_by_blocks(local_scores, observed_blocks)
    tp = fp = fn = tn = 0
    token_tp = token_fp = token_fn = token_tn = 0
    pred_blocks: List[int] = []
    gt_blocks: List[int] = []
    block_scores: List[float] = []

    for original, scores, origins, events in zip(
        original_blocks,
        score_blocks,
        origin_maps_per_block,
        gt_events_per_block,
    ):
        block_score = float(np.min(scores)) if scores else 1.0
        if threshold_mode in strict_token_modes:
            # The prior detector flags tokens with score < tau_e. The common
            # block-level alarm is the union of those original token alarms.
            pred = int(any(float(score) < float(token_threshold) for score in scores))
        else:
            pred = int(block_score <= float(block_threshold))
        label = int(bool(events))
        pred_blocks.append(pred)
        gt_blocks.append(label)
        block_scores.append(block_score)
        if label and pred:
            tp += 1
        elif label:
            fn += 1
        elif pred:
            fp += 1
        else:
            tn += 1

        token_counts = _evaluate_token_predictions(
            original,
            scores,
            origins,
            events,
            token_threshold,
            strict=threshold_mode in strict_token_modes,
        )
        token_tp += token_counts["token_tp"]
        token_fp += token_counts["token_fp"]
        token_fn += token_counts["token_fn"]
        token_tn += token_counts["token_tn"]

    token_precision = _safe_div(token_tp, token_tp + token_fp)
    token_recall = _safe_div(token_tp, token_tp + token_fn)
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": _safe_div(tp, tp + fn),
        "block_far": _safe_div(fp, fp + tn),
        "pred_blocks": pred_blocks,
        "gt_blocks": gt_blocks,
        "block_scores": block_scores,
        "token_tp": token_tp,
        "token_fp": token_fp,
        "token_fn": token_fn,
        "token_tn": token_tn,
        "token_precision": token_precision,
        "token_recall": token_recall,
        "token_f1": _safe_div(
            2.0 * token_precision * token_recall,
            token_precision + token_recall,
        ),
        "token_far": _safe_div(token_fp, token_fp + token_tn),
    }


def _evaluate_token_predictions(
    original_block: Sequence[int],
    observed_scores: Sequence[float],
    origin_map: Sequence[int],
    events: Sequence[EditEvent],
    threshold: float,
    *,
    strict: bool,
) -> Dict[str, int]:
    predicted_by_origin = {index: False for index in range(len(original_block))}
    inserted_predictions: List[bool] = []
    for origin, score in zip(origin_map, observed_scores):
        suspicious = (
            bool(float(score) < float(threshold))
            if strict
            else bool(float(score) <= float(threshold))
        )
        if int(origin) >= 0:
            predicted_by_origin[int(origin)] = (
                predicted_by_origin.get(int(origin), False) or suspicious
            )
        else:
            inserted_predictions.append(suspicious)

    positive_origins = {
        int(event.loc[1])
        for event in events
        if event.etype != "insert" and event.loc[0] == "payload"
    }
    inserted_count = sum(1 for event in events if event.etype == "insert")
    token_tp = token_fp = token_fn = token_tn = 0
    for origin in range(len(original_block)):
        pred = predicted_by_origin.get(origin, False)
        label = origin in positive_origins
        if label and pred:
            token_tp += 1
        elif label:
            token_fn += 1
        elif pred:
            token_fp += 1
        else:
            token_tn += 1
    for pred in inserted_predictions[:inserted_count]:
        if pred:
            token_tp += 1
        else:
            token_fn += 1
    for pred in inserted_predictions[inserted_count:]:
        if pred:
            token_fp += 1
        else:
            token_tn += 1
    return {
        "token_tp": token_tp,
        "token_fp": token_fp,
        "token_fn": token_fn,
        "token_tn": token_tn,
    }


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0
