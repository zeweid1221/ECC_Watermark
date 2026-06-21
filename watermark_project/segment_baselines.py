from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .config import GenerationSetting, KGWConfig, RunConfig, SegmentBaselineConfig
from .edits import EditEvent, apply_token_edits_to_blocks
from .kgw_generator import KgwGenerationResult, KgwGenerator
from .kgw_evaluator import token_scores_red
from .modeling import BaseLanguageModel
from .ppl import compute_text_perplexity


ALIGATOR_ADAPTED_SOURCE_NOTE = (
    "Adapted from llm-watermark-location-main/wm/detector.py and "
    "llm-watermark-location-main/cpp_src/aligator.cpp because the original "
    "repository in this workspace does not include a built importable aligator extension."
)


@dataclass
class SegmentBaselineGenerationResult:
    prompt: str
    suffix_text: str
    generated_token_ids: List[int]
    clean_blocks: List[List[int]]


def run_segment_baseline_suite(
    model: BaseLanguageModel,
    prompts: Sequence[str],
    run_config: RunConfig,
    override_logit_bias: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    cfg = run_config.segment_baselines
    target_blocks = cfg.target_blocks if cfg.target_blocks is not None else run_config.target_blocks
    total_tokens = cfg.total_tokens if cfg.total_tokens is not None else cfg.block_len * target_blocks
    baseline_logit_bias = (
        float(override_logit_bias)
        if override_logit_bias is not None
        else float(run_config.kgw_logit_bias)
        if run_config.kgw_logit_bias is not None
        else float(cfg.approx_hard_logit_bias)
    )
    baseline_kgw_cfg = KGWConfig(block_len=cfg.block_len, seed_count=run_config.kgw.seed_count, seed_offset=run_config.kgw.seed_offset)
    generator = KgwGenerator(model, baseline_kgw_cfg)
    setting = GenerationSetting(
        scheme="kgw",
        watermark_mode="soft",
        adaptive=None,
        target_blocks=target_blocks,
        max_new_tokens=max(run_config.max_new_tokens, total_tokens),
        seed=run_config.generation_seed + cfg.generation_seed_offset,
        logit_bias=baseline_logit_bias,
    )
    generated = generate_clean_baseline_sequences(generator, prompts, setting, total_tokens, cfg.block_len)
    ppl = compute_text_perplexity(model, [x.suffix_text for x in generated], max_length=max(run_config.max_new_tokens, total_tokens))

    summary_rows: List[Dict[str, Any]] = []
    detail_rows: List[Dict[str, Any]] = []
    payload = {
        "baseline_source_scheme": "clean_token_sequence",
        "setting": {
            "watermark_mode": "soft",
            "logit_bias": baseline_logit_bias,
            "target_blocks": target_blocks,
            "block_len": cfg.block_len,
            "total_tokens": total_tokens,
            "score_type": cfg.score_type,
            "aol_backend": cfg.aol_backend,
            "aol_aligator_source": cfg.aol_aligator_source,
        },
    }
    for attack_budget in run_config.attack_max_edits_per_blocks:
        for edit_rate in run_config.edit_rates:
            attacked_sequences = build_attacked_sequence_records(
                generated=generated,
                model=model,
                edit_rate=edit_rate,
                attack_max_edits_per_block=attack_budget,
                edit_count_mode=run_config.edit_count_mode,
                seed=run_config.generation_seed + int(edit_rate * 1000) + 20000 * attack_budget,
            )
            for method in cfg.methods:
                summary, rows = evaluate_segment_baseline_method(
                    method=method,
                    attacked_sequences=attacked_sequences,
                    baseline_cfg=cfg,
                    kgw_cfg=baseline_kgw_cfg,
                    logit_bias=baseline_logit_bias,
                    model_vocab_size=model.vocab_size,
                    attack_budget=attack_budget,
                    edit_rate=edit_rate,
                    edit_count_mode=run_config.edit_count_mode,
                    ppl=ppl,
                )
                summary_rows.append(summary)
                detail_rows.extend(rows)
    return summary_rows, detail_rows, payload


def generate_clean_baseline_sequences(
    generator: KgwGenerator,
    prompts: Sequence[str],
    setting: GenerationSetting,
    total_tokens: int,
    block_len: int,
) -> List[SegmentBaselineGenerationResult]:
    outputs: List[SegmentBaselineGenerationResult] = []
    for idx, prompt in enumerate(prompts):
        prompt_setting = GenerationSetting(
            scheme=setting.scheme,
            watermark_mode=setting.watermark_mode,
            adaptive=setting.adaptive,
            target_blocks=setting.target_blocks,
            max_new_tokens=max(setting.max_new_tokens, total_tokens),
            seed=setting.seed + idx,
            logit_bias=setting.logit_bias,
        )
        generated = generator.generate_one(prompt, prompt_setting)
        token_ids = [int(x) for x in generated.generated_token_ids[:total_tokens]]
        if len(token_ids) < total_tokens:
            token_ids.extend(repeat_last_non_special(token_ids, generator.model, total_tokens - len(token_ids)))
        token_ids = token_ids[:total_tokens]
        clean_blocks = [
            token_ids[start : start + block_len]
            for start in range(0, len(token_ids), block_len)
        ]
        outputs.append(
            SegmentBaselineGenerationResult(
                prompt=prompt,
                suffix_text=generator.model.decode(token_ids, skip_special_tokens=True),
                generated_token_ids=token_ids,
                clean_blocks=clean_blocks,
            )
        )
    return outputs


def repeat_last_non_special(existing: Sequence[int], model: BaseLanguageModel, count: int) -> List[int]:
    if count <= 0:
        return []
    special = set(int(x) for x in model.all_special_ids)
    fallback = next((int(x) for x in reversed(existing) if int(x) not in special), None)
    if fallback is None:
        fallback = next((tid for tid in range(model.vocab_size) if tid not in special), model.pad_token_id)
    return [int(fallback)] * count


def build_attacked_sequence_records(
    generated: Sequence[SegmentBaselineGenerationResult],
    model: BaseLanguageModel,
    edit_rate: float,
    attack_max_edits_per_block: int,
    edit_count_mode: str,
    seed: int,
) -> List[Dict[str, Any]]:
    special = set(int(x) for x in model.all_special_ids)
    vocab_ids = [token_id for token_id in range(model.vocab_size) if token_id not in special]
    records: List[Dict[str, Any]] = []
    for idx, result in enumerate(generated):
        attacked = apply_token_edits_to_blocks(
            token_blocks=[list(block) for block in result.clean_blocks],
            edit_rate=edit_rate,
            max_edits_per_block=attack_max_edits_per_block,
            edit_count_mode=edit_count_mode,
            vocab_ids=vocab_ids,
            rng=random.Random(seed + idx),
        )
        spans = []
        cursor = 0
        for block in attacked["observed_blocks"]:
            start = cursor
            end = start + len(block)
            spans.append((start, end))
            cursor = end
        records.append(
            {
                "prompt": result.prompt,
                "suffix_text": result.suffix_text,
                "clean_blocks": [list(block) for block in result.clean_blocks],
                "observed_blocks": attacked["observed_blocks"],
                "gt_events_per_block": attacked["gt_events_per_block"],
                "observed_sequence": attacked["observed_full_sequence"],
                "observed_block_spans": spans,
            }
        )
    return records


def resolve_aol_variant(method: str, baseline_cfg: SegmentBaselineConfig) -> Tuple[str, str]:
    if method == "zhao_aol_aligator":
        return "zhao_aol_aligator", "aligator"
    if method == "zhao_aol_simple":
        return "zhao_aol", "simple"
    if method == "zhao_aol":
        backend = str(baseline_cfg.aol_backend or "simple").strip().lower()
        if backend not in {"simple", "aligator"}:
            raise ValueError(f"Unsupported aol_backend: {baseline_cfg.aol_backend}")
        return ("zhao_aol_aligator" if backend == "aligator" else "zhao_aol"), backend
    return method, ""


def resolve_aol_source_metadata(source_name: Optional[str]) -> Dict[str, Any]:
    if not source_name:
        return {
            "aol_source_used_exact": False,
            "aol_source_path": None,
            "aol_source_note": ALIGATOR_ADAPTED_SOURCE_NOTE,
        }
    source_root = Path(__file__).resolve().parents[1] / str(source_name)
    return {
        "aol_source_used_exact": False,
        "aol_source_path": str(source_root) if source_root.exists() else None,
        "aol_source_note": ALIGATOR_ADAPTED_SOURCE_NOTE,
    }


def aligator_estimates_python(
    values: Sequence[float],
    index_order: Sequence[int],
    sigma: float = 0.0,
    B: float = 1.0,
    delta: float = 1e-5,
    min_scale_exclusive: int = 4,
) -> np.ndarray:
    """
    Python adaptation of llm-watermark-location-main/cpp_src/aligator.cpp.

    The original C++ code ignores scales k <= 4. For very short sequences that can
    leave the expert pool empty, so this port relaxes to all scales only when needed
    to keep the baseline usable in our short block-wise smoke settings.
    """
    y = np.asarray(values, dtype=np.float64)
    n = int(y.size)
    if n == 0:
        return y.copy()
    if n == 1:
        return np.zeros(1, dtype=np.float64)

    def build_pool(scale_floor: int) -> Tuple[List[List[Dict[str, float]]], int]:
        pool: List[List[Dict[str, float]]] = []
        pool_size = 0
        max_k = int(math.floor(math.log2(n)))
        for k in range(max_k + 1):
            stop = ((n + 1) >> k) - 1
            if stop < 1:
                break
            experts: List[Dict[str, float]] = []
            for _ in range(stop):
                experts.append({"prediction": 0.0, "loss": 0.0, "count": 0.0, "weight": 0.0})
                if k > scale_floor:
                    pool_size += 1
            pool.append(experts)
        return pool, pool_size

    def awake_set(t_one_based: int, scale_floor: int) -> List[int]:
        indices: List[int] = []
        max_k = int(math.floor(math.log2(max(1, t_one_based))))
        for k in range(max_k + 1):
            i = t_one_based >> k
            if (((i + 1) << k) - 1 > n) or (k <= scale_floor):
                indices.append(-1)
            else:
                indices.append(i)
        return indices

    pool, pool_size = build_pool(min_scale_exclusive)
    effective_scale_floor = min_scale_exclusive
    if pool_size <= 0:
        effective_scale_floor = -1
        pool, pool_size = build_pool(effective_scale_floor)
    pool_size = max(1, pool_size)

    estimates = np.zeros(n, dtype=np.float64)
    prev_pred = 0.0
    loss_norm = 2.0 * (B + sigma * math.sqrt(max(1e-12, math.log(max(2.0 * n / max(delta, 1e-12), 1.0))))) ** 2
    index_order = [int(x) for x in index_order]
    for t in range(n):
        idx = index_order[t]
        y_curr = float(y[idx])
        awake = awake_set(idx + 1, effective_scale_floor)
        output = 0.0
        normalizer = 0.0
        active: List[Tuple[int, int]] = []
        for k, awake_idx in enumerate(awake):
            if awake_idx == -1:
                continue
            i = awake_idx - 1
            if i < 0 or k >= len(pool) or i >= len(pool[k]):
                continue
            expert = pool[k][i]
            if expert["weight"] == 0.0:
                expert["weight"] = 1.0 / pool_size
                expert["prediction"] = prev_pred
            output += expert["weight"] * expert["prediction"]
            normalizer += expert["weight"]
            active.append((k, i))
        forecast = output / normalizer if normalizer > 0 else prev_pred
        estimates[idx] = forecast

        losses: List[Tuple[Tuple[int, int], float]] = []
        exp_norm = 0.0
        for k, i in active:
            expert = pool[k][i]
            loss = ((y_curr - expert["prediction"]) ** 2) / max(loss_norm, 1e-12)
            losses.append(((k, i), loss))
            exp_norm += expert["weight"] * math.exp(-loss)
        exp_norm = max(exp_norm, 1e-12)
        for (k, i), loss in losses:
            expert = pool[k][i]
            expert["weight"] = expert["weight"] * math.exp(-loss) * max(normalizer, 1e-12) / exp_norm
            count = expert["count"]
            expert["prediction"] = ((expert["prediction"] * count) + y_curr) / (count + 1.0)
            expert["count"] = count + 1.0
        prev_pred = y_curr
    return estimates


def aol_aligator_denoised_scores(
    scores: Sequence[float],
    iterations: int,
    source_name: Optional[str],
) -> Tuple[np.ndarray, Dict[str, Any]]:
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        return arr, resolve_aol_source_metadata(source_name)
    rng = random.Random(20260511 + arr.size + int(iterations))
    starts = [rng.randrange(arr.size) for _ in range(max(1, int(iterations)))]
    preds: List[np.ndarray] = []
    for shift in starts:
        shifted = np.roll(arr, -int(shift))
        forward = aligator_estimates_python(shifted, list(range(shifted.size)))
        backward = aligator_estimates_python(shifted, list(reversed(range(shifted.size))))
        denoised_shifted = np.nanmean(np.stack([forward, backward], axis=0), axis=0)
        preds.append(np.roll(denoised_shifted, int(shift)))
    return np.mean(np.stack(preds, axis=0), axis=0), resolve_aol_source_metadata(source_name)


def evaluate_segment_baseline_method(
    method: str,
    attacked_sequences: Sequence[Dict[str, Any]],
    baseline_cfg: SegmentBaselineConfig,
    kgw_cfg: KGWConfig,
    logit_bias: float,
    model_vocab_size: int,
    attack_budget: int,
    edit_rate: float,
    edit_count_mode: str,
    ppl: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    scheme_name, aol_backend = resolve_aol_variant(method, baseline_cfg)
    if scheme_name not in {"zhao_aol", "zhao_aol_aligator", "waterseeker"}:
        raise ValueError(f"Unknown segment baseline method: {method}")
    tp = fp = fn = tn = 0
    used_sequences = 0
    valid_blocks_total = 0
    event_total_overall = 0
    event_total_sub = 0
    event_total_insert = 0
    event_total_delete = 0
    detail_rows: List[Dict[str, Any]] = []
    threshold_records: List[Tuple[float, float]] = []
    for seq_idx, record in enumerate(attacked_sequences):
        observed_sequence = record["observed_sequence"]
        spans = record["observed_block_spans"]
        gt_events = record["gt_events_per_block"]
        if not observed_sequence or not spans:
            detail_rows.append(
                {
                    "scheme": scheme_name,
                    "baseline_source_scheme": "clean_token_sequence",
                    "block_len": baseline_cfg.block_len,
                    "watermark_mode": "soft",
                    "logit_bias": float(logit_bias),
                    "adaptive": None,
                    "edit_rate": edit_rate,
                    "attack_max_edits_per_block": attack_budget,
                    "edit_count_mode": edit_count_mode,
                    "decoder_budget": None,
                    "score_type": baseline_cfg.score_type,
                    "aol_backend": aol_backend or None,
                    "aol_iterations": baseline_cfg.aol_iterations if scheme_name.startswith("zhao_aol") else None,
                    "aol_source_used_exact": None,
                    "aol_source_path": None,
                    "sequence_index": seq_idx,
                    "used": False,
                    "skip_reason": "empty_observed_sequence",
                }
            )
            continue
        used_sequences += 1
        valid_blocks_total += len(record["clean_blocks"])
        scores = compute_token_anomaly_scores(
            observed_sequence,
            kgw_cfg,
            model_vocab_size=model_vocab_size,
            score_type=baseline_cfg.score_type,
        )
        if scheme_name.startswith("zhao_aol"):
            if aol_backend == "aligator":
                token_scores, source_meta = aol_aligator_denoised_scores(
                    scores,
                    iterations=baseline_cfg.aol_iterations,
                    source_name=baseline_cfg.aol_aligator_source,
                )
            else:
                token_scores = aol_denoised_scores(scores, iterations=baseline_cfg.aol_iterations)
                source_meta = {
                    "aol_source_used_exact": False,
                    "aol_source_path": None,
                    "aol_source_note": "simple_geometric_cover_fallback",
                }
            token_threshold = baseline_cfg.aol_token_threshold
            if token_threshold is None:
                token_threshold = default_token_threshold(token_scores, top_fraction=baseline_cfg.aol_top_mean_fraction)
            predicted_positions = [idx for idx, value in enumerate(token_scores.tolist()) if value > token_threshold]
            predicted_spans = merge_positions_to_fragments(predicted_positions, min_fragment_len=1)
            block_scores = [top_mean_score(token_scores[start:end], baseline_cfg.aol_top_mean_fraction) if end > start else 0.0 for start, end in spans]
            block_threshold = baseline_cfg.aol_block_threshold
            if block_threshold is None:
                block_threshold = float(token_threshold)
            block_preds = [
                int(span_overlap_tokens((start, end), predicted_spans) >= 1)
                for start, end in spans
            ]
            threshold_records.append((float(token_threshold), float(block_threshold)))
            method_meta = {
                "aol_backend": aol_backend,
                "aol_iterations": baseline_cfg.aol_iterations,
                **source_meta,
                "token_threshold": float(token_threshold),
                "block_threshold": float(block_threshold),
                "predicted_spans": predicted_spans,
                "block_scores": block_scores,
            }
        else:
            window = baseline_cfg.waterseeker_window or max(baseline_cfg.block_len, baseline_cfg.block_len * 2)
            score_list = waterseeker_score_list(scores, window=window)
            coarse_spans, threshold = waterseeker_coarse_spans(
                score_list=score_list,
                score_window=window,
                top_k=baseline_cfg.waterseeker_top_k,
                connect_tolerance=baseline_cfg.waterseeker_connect_tolerance or baseline_cfg.block_len,
                min_fragment_len=baseline_cfg.waterseeker_min_fragment_len,
            )
            predicted_spans = waterseeker_local_traverse(
                token_scores=np.asarray(scores, dtype=np.float64),
                coarse_spans=coarse_spans,
                window=window,
                threshold=float(threshold),
            )
            block_preds = [
                int(span_overlap_tokens((start, end), predicted_spans) >= baseline_cfg.waterseeker_block_overlap_tokens)
                for start, end in spans
            ]
            threshold_records.append((float(threshold), float(threshold)))
            method_meta = {
                "aol_backend": None,
                "aol_iterations": None,
                "aol_source_used_exact": None,
                "aol_source_path": None,
                "aol_source_note": None,
                "token_threshold": float(threshold),
                "block_threshold": float(threshold),
                "predicted_spans": predicted_spans,
                "coarse_spans": coarse_spans,
            }
        block_labels = [int(len(events) > 0) for events in gt_events]
        seq_counts = block_confusion_counts(block_labels, block_preds)
        tp += seq_counts["TP"]
        fp += seq_counts["FP"]
        fn += seq_counts["FN"]
        tn += seq_counts["TN"]
        event_total_overall += int(sum(len(events) for events in gt_events))
        event_total_sub += int(sum(1 for events in gt_events for ev in events if ev.etype == "sub"))
        event_total_insert += int(sum(1 for events in gt_events for ev in events if ev.etype == "insert"))
        event_total_delete += int(sum(1 for events in gt_events for ev in events if ev.etype == "delete"))
        detail_rows.append(
            {
                "scheme": scheme_name,
                "baseline_source_scheme": "clean_token_sequence",
                "block_len": baseline_cfg.block_len,
                "watermark_mode": "soft",
                "logit_bias": float(logit_bias),
                "adaptive": None,
                "edit_rate": edit_rate,
                "attack_max_edits_per_block": attack_budget,
                "edit_count_mode": edit_count_mode,
                "decoder_budget": None,
                "score_type": baseline_cfg.score_type,
                "sequence_index": seq_idx,
                "used": True,
                "num_valid_blocks": len(record["clean_blocks"]),
                "num_observed_tokens": len(observed_sequence),
                "TP": seq_counts["TP"],
                "FP": seq_counts["FP"],
                "FN": seq_counts["FN"],
                "TN": seq_counts["TN"],
                "block_tpr": safe_div(seq_counts["TP"], seq_counts["TP"] + seq_counts["FN"]),
                "block_far": safe_div(seq_counts["FP"], seq_counts["FP"] + seq_counts["TN"]),
                "block_precision": safe_div(seq_counts["TP"], seq_counts["TP"] + seq_counts["FP"]),
                "block_recall": safe_div(seq_counts["TP"], seq_counts["TP"] + seq_counts["FN"]),
                "block_f1": safe_f1(seq_counts["TP"], seq_counts["FP"], seq_counts["FN"]),
                "event_total_overall": int(sum(len(events) for events in gt_events)),
                "event_total_sub": int(sum(1 for events in gt_events for ev in events if ev.etype == "sub")),
                "event_total_insert": int(sum(1 for events in gt_events for ev in events if ev.etype == "insert")),
                "event_total_delete": int(sum(1 for events in gt_events for ev in events if ev.etype == "delete")),
                **method_meta,
            }
        )
    mean_token_threshold = float(np.mean([x for x, _ in threshold_records])) if threshold_records else math.nan
    mean_block_threshold = float(np.mean([y for _, y in threshold_records])) if threshold_records else math.nan
    summary = {
        "scheme": scheme_name,
        "baseline_source_scheme": "clean_token_sequence",
        "block_len": baseline_cfg.block_len,
        "watermark_mode": "soft",
        "logit_bias": float(logit_bias),
        "adaptive": None,
        "edit_rate": edit_rate,
        "attack_max_edits_per_block": attack_budget,
        "edit_count_mode": edit_count_mode,
        "decoder_budget": None,
        "ppl": ppl,
        "num_sequences_total": len(attacked_sequences),
        "num_sequences_used": used_sequences,
        "num_sequences_skipped": len(attacked_sequences) - used_sequences,
        "mean_valid_blocks_per_used_sequence": safe_div(valid_blocks_total, used_sequences),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": safe_div(tp, tp + fn),
        "block_far": safe_div(fp, fp + tn),
        "block_precision": safe_div(tp, tp + fp),
        "block_recall": safe_div(tp, tp + fn),
        "block_f1": safe_f1(tp, fp, fn),
        "event_total_overall": event_total_overall,
        "event_total_sub": event_total_sub,
        "event_total_insert": event_total_insert,
        "event_total_delete": event_total_delete,
        "codeword_recovery_acc": math.nan,
        "localization_acc_overall": math.nan,
        "loc_total_overall": 0,
        "event_coverage_overall": math.nan,
        "event_coverage_sub": math.nan,
        "event_coverage_insert": math.nan,
        "event_coverage_delete": math.nan,
        "mean_candidate_size": math.nan,
        "mean_red_score": float(np.mean([
            np.mean(compute_token_anomaly_scores(
                rec["observed_sequence"],
                kgw_cfg,
                model_vocab_size=model_vocab_size,
                score_type=baseline_cfg.score_type,
            ))
            for rec in attacked_sequences
            if rec["observed_sequence"]
        ])) if attacked_sequences else math.nan,
        "mean_observed_block_len": float(np.mean([len(block) for rec in attacked_sequences for block in rec["observed_blocks"]])) if attacked_sequences else math.nan,
        "token_tp": math.nan,
        "token_fp": math.nan,
        "token_fn": math.nan,
        "token_tn": math.nan,
        "token_precision": math.nan,
        "token_recall": math.nan,
        "token_f1": math.nan,
        "token_far": math.nan,
        "score_type": baseline_cfg.score_type,
        "aol_backend": aol_backend or None,
        "aol_iterations": baseline_cfg.aol_iterations if scheme_name.startswith("zhao_aol") else None,
        "aol_source_used_exact": (
            any(bool(row.get("aol_source_used_exact")) for row in detail_rows)
            if scheme_name.startswith("zhao_aol")
            else None
        ),
        "aol_source_path": (
            next((row.get("aol_source_path") for row in detail_rows if row.get("aol_source_path")), None)
            if scheme_name.startswith("zhao_aol")
            else None
        ),
        "aol_source_note": (
            next((row.get("aol_source_note") for row in detail_rows if row.get("aol_source_note")), None)
            if scheme_name.startswith("zhao_aol")
            else None
        ),
        "token_threshold": mean_token_threshold,
        "block_threshold": mean_block_threshold,
    }
    return summary, detail_rows


def compute_token_anomaly_scores(
    observed_sequence: Sequence[int],
    kgw_cfg: KGWConfig,
    model_vocab_size: int,
    score_type: str,
) -> np.ndarray:
    if score_type not in {"watermark_deficit", "token_surprisal_proxy"}:
        raise ValueError(f"Unsupported segment baseline score_type: {score_type}")
    return token_scores_red(observed_sequence, kgw_cfg, vocab_size=int(model_vocab_size))


def aol_denoised_scores(scores: Sequence[float], iterations: int) -> np.ndarray:
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        return arr
    rng = random.Random(20260510 + arr.size + int(iterations))
    if iterations <= 1:
        shifts = [0]
    else:
        shifts = [rng.randrange(arr.size) for _ in range(iterations)]
    preds = []
    for shift in shifts:
        shifted = np.roll(arr, -int(shift))
        denoised_shifted = geometric_cover_denoise(shifted)
        preds.append(np.roll(denoised_shifted, int(shift)))
    return np.mean(np.stack(preds, axis=0), axis=0)


def geometric_cover_denoise(values: np.ndarray) -> np.ndarray:
    n = values.size
    if n == 0:
        return values.astype(np.float64)
    per_token_sums = np.zeros(n, dtype=np.float64)
    per_token_weights = np.zeros(n, dtype=np.float64)
    max_power = int(math.floor(math.log2(max(1, n))))
    for power in range(max_power + 1):
        interval_len = 2 ** power
        weight = 1.0 / (power + 1.0)
        start = 0
        while start < n:
            end = min(n, start + interval_len)
            mean_value = float(np.mean(values[start:end]))
            per_token_sums[start:end] += weight * mean_value
            per_token_weights[start:end] += weight
            start += interval_len
    per_token_weights[per_token_weights == 0] = 1.0
    return per_token_sums / per_token_weights


def moving_average_circular(values: np.ndarray, window: int) -> np.ndarray:
    if values.size == 0:
        return values
    if window <= 1:
        return values.astype(np.float64, copy=True)
    out = np.zeros_like(values, dtype=np.float64)
    half = window // 2
    for idx in range(values.size):
        positions = [(idx + offset) % values.size for offset in range(-half, window - half)]
        out[idx] = float(np.mean(values[positions]))
    return out


def top_mean_score(values: Sequence[float], fraction: float) -> float:
    arr = np.asarray(list(values), dtype=np.float64)
    if arr.size == 0:
        return 0.0
    k = max(1, int(math.ceil(arr.size * max(min(fraction, 1.0), 0.0 if fraction is not None else 0.0))))
    return float(np.mean(np.sort(arr)[-k:]))


def default_token_threshold(scores: Sequence[float], top_fraction: float) -> float:
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    mu = float(arr.mean())
    top_mean = top_mean_score(arr, top_fraction)
    return mu + 0.5 * (top_mean - mu)


def default_block_threshold(scores: Sequence[float], top_fraction: float) -> float:
    return default_token_threshold(scores, top_fraction)


def waterseeker_score_list(scores: Sequence[float], window: int) -> np.ndarray:
    arr = np.asarray(scores, dtype=np.float64)
    if arr.size == 0:
        return arr
    window = max(1, int(window))
    if arr.size <= window:
        return np.asarray([float(np.mean(arr))], dtype=np.float64)
    return np.asarray(
        [float(np.mean(arr[start : start + window])) for start in range(0, arr.size - window + 1)],
        dtype=np.float64,
    )


def waterseeker_coarse_spans(
    score_list: Sequence[float],
    score_window: int,
    top_k: int,
    connect_tolerance: int,
    min_fragment_len: int,
) -> Tuple[List[Tuple[int, int]], float]:
    arr = np.asarray(score_list, dtype=np.float64)
    if arr.size == 0:
        return [], 0.0
    mu = float(arr.mean())
    top_k = max(1, min(int(top_k), arr.size))
    top_mean = float(np.mean(np.sort(arr)[-top_k:]))
    threshold = mu + 0.5 * (top_mean - mu)
    outliers = [idx for idx, value in enumerate(arr.tolist()) if value >= threshold]
    fragments = merge_positions_to_fragments(outliers, min_fragment_len=min_fragment_len)
    connected = connect_fragments(fragments, connect_tolerance=connect_tolerance)
    coarse_spans = [(start, min(end + score_window, arr.size + score_window - 1)) for start, end in connected]
    return coarse_spans, threshold


def waterseeker_local_traverse(
    token_scores: np.ndarray,
    coarse_spans: Sequence[Tuple[int, int]],
    window: int,
    threshold: float,
) -> List[Tuple[int, int]]:
    n = token_scores.size
    predicted: List[Tuple[int, int]] = []
    for start_coarse, end_coarse in coarse_spans:
        best_score = float("-inf")
        best_span: Optional[Tuple[int, int]] = None
        start_candidates = range(max(0, start_coarse), min(n, start_coarse + window))
        end_min = max(1, end_coarse - window)
        end_candidates = range(max(1, end_min), min(n, end_coarse) + 1)
        for start in start_candidates:
            for end in end_candidates:
                if end <= start:
                    continue
                score = float(np.mean(token_scores[start:end]))
                if score > best_score:
                    best_score = score
                    best_span = (start, end)
        if best_span is not None and best_score > threshold:
            predicted.append(best_span)
    return connect_fragments(sorted(predicted), connect_tolerance=max(1, window // 2))


def merge_positions_to_fragments(positions: Sequence[int], min_fragment_len: int) -> List[Tuple[int, int]]:
    if not positions:
        return []
    frags: List[Tuple[int, int]] = []
    start = prev = int(positions[0])
    for pos in positions[1:]:
        pos = int(pos)
        if pos == prev + 1:
            prev = pos
            continue
        if prev - start + 1 >= min_fragment_len:
            frags.append((start, prev + 1))
        start = prev = pos
    if prev - start + 1 >= min_fragment_len:
        frags.append((start, prev + 1))
    return frags


def connect_fragments(fragments: Sequence[Tuple[int, int]], connect_tolerance: int) -> List[Tuple[int, int]]:
    if not fragments:
        return []
    merged: List[Tuple[int, int]] = [tuple(fragments[0])]
    for start, end in fragments[1:]:
        last_start, last_end = merged[-1]
        if start - last_end <= connect_tolerance:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def span_overlap_tokens(block_span: Tuple[int, int], predicted_spans: Sequence[Tuple[int, int]]) -> int:
    start, end = block_span
    overlap = 0
    for p_start, p_end in predicted_spans:
        overlap = max(overlap, max(0, min(end, p_end) - max(start, p_start)))
    return overlap


def block_confusion_counts(labels: Sequence[int], preds: Sequence[int]) -> Dict[str, int]:
    tp = fp = fn = tn = 0
    for label, pred in zip(labels, preds):
        if label and pred:
            tp += 1
        elif label and not pred:
            fn += 1
        elif (not label) and pred:
            fp += 1
        else:
            tn += 1
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


def safe_div(num: float, den: float) -> float:
    return float(num) / float(den) if den else 0.0


def safe_f1(tp: int, fp: int, fn: int) -> float:
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    return 2.0 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
