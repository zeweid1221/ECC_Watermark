from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .config import ECCConfig, GenerationProtocolConfig, GenerationSetting
from .ecc_detector import EccCodebook, decode_clean_structural_sequence
from .modeling import (
    BaseLanguageModel,
    apply_repetition_penalty,
    build_ascii_token_ban_mask,
    render_prompt_for_model,
    sample_token_from_logits,
    stable_hash_int,
)
from .partitioning import VocabularyPartition


def logsumexp_np(values: np.ndarray) -> float:
    if values.size == 0:
        return float("-inf")
    m = float(values.max())
    if not math.isfinite(m):
        return m
    return m + float(np.log(np.exp(values - m).sum()))


@dataclass
class EccRuntimeState:
    current_bits: List[int] = field(default_factory=list)
    payload_count_since_boundary: int = 0
    overflow_count: int = 0
    invalid_prefix_flag: bool = False
    completed_blocks: int = 0
    empty_boundary_count: int = 0
    block_summaries: List[Dict[str, Any]] = field(default_factory=list)
    current_codeword: Optional[List[int]] = None
    chosen_codewords: List[List[int]] = field(default_factory=list)


@dataclass
class EccGenerationResult:
    prompt: str
    full_text: str
    suffix_text: str
    generated_token_ids: List[int]
    generated_bucket_seq: List[int]
    structural_seq: List[int]
    decoded_clean: Dict[str, Any]
    runtime_state: EccRuntimeState
    raw_top_trace: List[Dict[str, Any]]
    prompt_token_ids: List[int] = field(default_factory=list)
    user_prompt: str = ""
    rendered_prompt: str = ""
    prompt_mode: str = "raw"
    stop_reason: str = "unknown"


class EccGenerator:
    def __init__(self, model: BaseLanguageModel, partition: VocabularyPartition, config: ECCConfig):
        self.model = model
        self.partition = partition
        self.config = config
        self.codebook = EccCodebook(block_len=config.block_len, vt_a=config.vt_a)
        self.prefix_to_allowed_next_bits: Dict[Tuple[int, ...], Set[int]] = defaultdict(set)
        for codeword in self.codebook.feasible:
            for idx in range(len(codeword)):
                self.prefix_to_allowed_next_bits[tuple(codeword[:idx])].add(int(codeword[idx]))
        self.bucket_masks = {
            bucket: (self.partition.token_to_bucket == bucket)
            for bucket in (0, 1, 2)
        }
        self.always_ban_mask = np.zeros(self.model.vocab_size, dtype=bool)
        self.always_ban_mask[np.where(self.partition.token_to_bucket < 0)[0]] = True
        for token_id in self.partition.banned_ids:
            self.always_ban_mask[int(token_id)] = True
        self._ascii_ban_masks: Dict[bool, np.ndarray] = {}

    def allowed_next_bits(self, prefix_bits: Sequence[int], adaptive: bool, fixed_codeword: Optional[Sequence[int]]) -> Set[int]:
        prefix = tuple(int(x) for x in prefix_bits)
        if adaptive:
            return set(self.prefix_to_allowed_next_bits.get(prefix, set()))
        if fixed_codeword is None:
            return set()
        pos = len(prefix_bits)
        if pos >= len(fixed_codeword):
            return set()
        return {int(fixed_codeword[pos])}

    def choose_fixed_codeword(self, logits: np.ndarray, rng: random.Random) -> List[int]:
        bucket_scores = {
            bit: logsumexp_np(logits[self.bucket_masks[bit] & ~self.always_ban_mask])
            for bit in (0, 1)
        }
        preferred_bit = 0 if bucket_scores[0] >= bucket_scores[1] else 1
        candidates = [cw for cw in self.codebook.feasible if int(cw[0]) == preferred_bit]
        if not candidates:
            candidates = list(self.codebook.feasible)
        return list(rng.choice(candidates))

    def update_runtime_state(self, state: EccRuntimeState, bucket_label: int) -> None:
        if bucket_label in (0, 1):
            state.payload_count_since_boundary += 1
            if len(state.current_bits) < self.config.block_len:
                state.current_bits.append(int(bucket_label))
                if len(state.current_bits) < self.config.block_len and tuple(state.current_bits) not in self.prefix_to_allowed_next_bits:
                    state.invalid_prefix_flag = True
            else:
                state.overflow_count += 1
            return
        if bucket_label == 2:
            is_complete = len(state.current_bits) == self.config.block_len
            is_no_overflow = state.overflow_count == 0
            is_exact_payload_count = state.payload_count_since_boundary == self.config.block_len
            is_valid_codeword = tuple(state.current_bits) in self.codebook.feasible_set if is_complete else False
            is_valid_closed_block = bool(is_complete and is_no_overflow and is_exact_payload_count and is_valid_codeword)
            if state.payload_count_since_boundary > 0 or state.current_bits:
                state.block_summaries.append(
                    {
                        "bits_seen_before_boundary": int(state.payload_count_since_boundary),
                        "bits_prefix_capped": state.current_bits.copy(),
                        "overflow_count": int(state.overflow_count),
                        "invalid_prefix_flag": bool(state.invalid_prefix_flag),
                        "is_valid_codeword": bool(is_valid_codeword),
                        "is_valid_closed_block": bool(is_valid_closed_block),
                    }
                )
            else:
                state.empty_boundary_count += 1
            if is_valid_closed_block:
                state.completed_blocks += 1
            state.current_bits = []
            state.payload_count_since_boundary = 0
            state.overflow_count = 0
            state.invalid_prefix_flag = False
            state.current_codeword = None

    def apply_hard_control(
        self,
        logits: np.ndarray,
        state: EccRuntimeState,
        allowed_bits: Set[int],
        boundary_bonus: float,
    ) -> np.ndarray:
        adjusted = logits.copy()
        allowed = np.zeros(self.model.vocab_size, dtype=bool)
        if len(state.current_bits) < self.config.block_len:
            for bit in allowed_bits:
                allowed |= self.bucket_masks[int(bit)]
        else:
            allowed |= self.bucket_masks[2]
            adjusted = adjusted + boundary_bonus * self.bucket_masks[2].astype(np.float64)
        allowed &= ~self.always_ban_mask
        adjusted[~allowed] = -1e9
        return adjusted

    def apply_soft_control(
        self,
        logits: np.ndarray,
        state: EccRuntimeState,
        allowed_bits: Set[int],
        logit_bias: float,
        boundary_bonus: float,
    ) -> np.ndarray:
        adjusted = logits.copy()
        adjusted[self.always_ban_mask] = -1e9
        if len(state.current_bits) < self.config.block_len:
            for bit in allowed_bits:
                adjusted = adjusted + logit_bias * self.bucket_masks[int(bit)].astype(np.float64)
            adjusted[self.bucket_masks[2]] = -1e9
        else:
            adjusted = adjusted + boundary_bonus * self.bucket_masks[2].astype(np.float64)
            adjusted[self.bucket_masks[0] | self.bucket_masks[1]] = -1e9
        return adjusted

    def generate_one(
        self,
        prompt: str,
        setting: GenerationSetting,
        protocol: Optional[GenerationProtocolConfig] = None,
    ) -> EccGenerationResult:
        if setting.scheme != "ecc":
            raise ValueError("EccGenerator only supports scheme='ecc'.")
        protocol = protocol or GenerationProtocolConfig()
        minimum_closed_block_tokens = setting.target_blocks * (self.config.block_len + 1)
        if setting.max_new_tokens < minimum_closed_block_tokens:
            raise ValueError(
                "max_new_tokens is too small for target_blocks closed ECC blocks: "
                f"need at least {minimum_closed_block_tokens}, got {setting.max_new_tokens}."
            )
        adaptive = bool(setting.adaptive)
        user_prompt, rendered_prompt, prompt_mode = render_prompt_for_model(self.model, prompt, protocol)
        prompt_hash = stable_hash_int(rendered_prompt)
        rng = random.Random(setting.seed ^ prompt_hash)
        token_rng = np.random.default_rng((setting.seed + prompt_hash) % (2**32))
        session = self.model.start_session(
            rendered_prompt,
            add_special_tokens=prompt_mode != "chat_template",
            clean=prompt_mode != "chat_template",
        )
        state = EccRuntimeState()
        generated_ids: List[int] = []
        generated_buckets: List[int] = []
        raw_top_trace: List[Dict[str, Any]] = []
        if protocol.ascii_token_filter not in self._ascii_ban_masks:
            self._ascii_ban_masks[protocol.ascii_token_filter] = build_ascii_token_ban_mask(
                self.model,
                protocol.ascii_token_filter,
            )
        ascii_ban_mask = self._ascii_ban_masks[protocol.ascii_token_filter]
        steps = 0

        def reached_target() -> bool:
            if protocol.stop_after == "feasible_blocks":
                return state.completed_blocks >= setting.target_blocks
            return len(state.block_summaries) >= setting.target_blocks

        while not reached_target() and steps < setting.max_new_tokens:
            raw_logits = session.next_logits()
            if not adaptive and state.current_codeword is None and len(state.current_bits) == 0:
                state.current_codeword = self.choose_fixed_codeword(raw_logits, rng)
                state.chosen_codewords.append(state.current_codeword.copy())
            allowed_bits = self.allowed_next_bits(state.current_bits, adaptive, state.current_codeword)
            if not allowed_bits and len(state.current_bits) < self.config.block_len:
                allowed_bits = {0, 1}
            raw_top_id = int(np.argmax(raw_logits))
            raw_top_bucket = int(self.partition.token_to_bucket[raw_top_id]) if raw_top_id < len(self.partition.token_to_bucket) else -1
            if setting.watermark_mode == "hard":
                adjusted_logits = self.apply_hard_control(
                    logits=raw_logits,
                    state=state,
                    allowed_bits=allowed_bits,
                    boundary_bonus=self.config.boundary_bonus,
                )
            else:
                adjusted_logits = self.apply_soft_control(
                    logits=raw_logits,
                    state=state,
                    allowed_bits=allowed_bits,
                    logit_bias=setting.resolved_logit_bias(),
                    boundary_bonus=self.config.boundary_bonus,
                )
            if protocol.ascii_token_filter:
                filtered_logits = adjusted_logits.copy()
                filtered_logits[ascii_ban_mask] = -1e9
                if np.any(np.isfinite(filtered_logits) & (filtered_logits > -1e8)):
                    adjusted_logits = filtered_logits
            adjusted_logits = apply_repetition_penalty(
                adjusted_logits,
                generated_ids,
                protocol.repetition_penalty,
            )
            next_id = sample_token_from_logits(adjusted_logits, token_rng, protocol)
            next_bucket = int(self.partition.token_to_bucket[next_id]) if next_id < len(self.partition.token_to_bucket) else -1
            session.append(next_id)
            generated_ids.append(next_id)
            generated_buckets.append(next_bucket)
            raw_top_trace.append(
                {
                    "step": steps,
                    "raw_top_id": raw_top_id,
                    "raw_top_bucket": raw_top_bucket,
                    "chosen_id": next_id,
                    "chosen_bucket": next_bucket,
                    "payload_len_before_step": len(state.current_bits),
                    "fixed_codeword": None if state.current_codeword is None else "".join(str(x) for x in state.current_codeword),
                }
            )
            self.update_runtime_state(state, next_bucket)
            steps += 1
        stop_reason = (
            f"target_{protocol.stop_after}"
            if reached_target()
            else "max_new_tokens"
        )
        full_token_ids = session.prompt_ids + generated_ids
        structural_seq = [bucket for bucket in generated_buckets if bucket in (0, 1, 2)]
        decoded_clean = decode_clean_structural_sequence(structural_seq, self.codebook)
        return EccGenerationResult(
            prompt=prompt,
            full_text=self.model.decode(full_token_ids, skip_special_tokens=True),
            suffix_text=self.model.decode(generated_ids, skip_special_tokens=True),
            generated_token_ids=generated_ids,
            generated_bucket_seq=generated_buckets,
            structural_seq=structural_seq,
            decoded_clean=decoded_clean,
            runtime_state=state,
            raw_top_trace=raw_top_trace,
            prompt_token_ids=[int(x) for x in session.prompt_ids],
            user_prompt=user_prompt,
            rendered_prompt=rendered_prompt,
            prompt_mode=prompt_mode,
            stop_reason=stop_reason,
        )

    def generate_many(
        self,
        prompts: Sequence[str],
        setting: GenerationSetting,
        protocol: Optional[GenerationProtocolConfig] = None,
    ) -> List[EccGenerationResult]:
        return [self.generate_one(prompt, setting, protocol=protocol) for prompt in prompts]
