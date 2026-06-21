from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import numpy as np

from .config import GenerationSetting, KGWConfig
from .modeling import BaseLanguageModel


def green_mask_for_seed(seed: int, vocab_size: int) -> np.ndarray:
    rng = np.random.default_rng(int(seed) & 0xFFFFFFFF)
    return rng.integers(0, 2, size=vocab_size, endpoint=False, dtype=np.int8).astype(bool)


def row_seed_from_suffix(generated_ids: Sequence[int], seed_count: int, seed_offset: int) -> int:
    end = max(0, len(generated_ids) - 1)
    start = max(0, end - seed_count)
    return int(sum(int(x) for x in generated_ids[start:end]) + seed_offset)


@dataclass
class KgwGenerationResult:
    prompt: str
    full_text: str
    suffix_text: str
    generated_token_ids: List[int]
    block_tokens: List[List[int]]
    raw_top_trace: List[Dict[str, Any]]


class KgwGenerator:
    def __init__(self, model: BaseLanguageModel, config: KGWConfig):
        self.model = model
        self.config = config
        self.always_ban_mask = np.zeros(self.model.vocab_size, dtype=bool)
        self.always_ban_mask[self.model.pad_token_id] = True
        self.always_ban_mask[self.model.eos_token_id] = False
        for token_id in self.model.all_special_ids:
            self.always_ban_mask[int(token_id)] = True
        self.always_ban_mask[self.model.eos_token_id] = True

    def apply_watermark(self, logits: np.ndarray, generated_ids: Sequence[int], setting: GenerationSetting) -> np.ndarray:
        adjusted = logits.copy()
        adjusted[self.always_ban_mask] = -1e9
        row_seed = row_seed_from_suffix(generated_ids, self.config.seed_count, self.config.seed_offset)
        green = green_mask_for_seed(row_seed, self.model.vocab_size)
        if setting.watermark_mode == "hard":
            adjusted[~green] = -1e9
        else:
            adjusted = adjusted + setting.resolved_logit_bias() * green.astype(np.float64)
        return adjusted

    def generate_one(self, prompt: str, setting: GenerationSetting) -> KgwGenerationResult:
        if setting.scheme != "kgw":
            raise ValueError("KgwGenerator only supports scheme='kgw'.")
        session = self.model.start_session(prompt)
        generated_ids: List[int] = []
        raw_top_trace: List[Dict[str, Any]] = []
        target_tokens = setting.target_blocks * self.config.block_len
        steps = 0
        while len(generated_ids) < target_tokens and steps < setting.max_new_tokens:
            raw_logits = session.next_logits()
            raw_top_id = int(np.argmax(raw_logits))
            adjusted = self.apply_watermark(raw_logits, generated_ids, setting)
            next_id = int(np.argmax(adjusted))
            session.append(next_id)
            generated_ids.append(next_id)
            raw_top_trace.append({"step": steps, "raw_top_id": raw_top_id, "chosen_id": next_id})
            steps += 1
        trimmed_len = (len(generated_ids) // self.config.block_len) * self.config.block_len
        generated_ids = generated_ids[:trimmed_len]
        blocks = [
            generated_ids[start : start + self.config.block_len]
            for start in range(0, len(generated_ids), self.config.block_len)
        ]
        full_text = self.model.decode(session.prompt_ids + generated_ids, skip_special_tokens=True)
        suffix_text = self.model.decode(generated_ids, skip_special_tokens=True)
        return KgwGenerationResult(
            prompt=prompt,
            full_text=full_text,
            suffix_text=suffix_text,
            generated_token_ids=generated_ids,
            block_tokens=blocks,
            raw_top_trace=raw_top_trace,
        )

    def generate_many(self, prompts: Sequence[str], setting: GenerationSetting) -> List[KgwGenerationResult]:
        return [self.generate_one(prompt, setting) for prompt in prompts]
