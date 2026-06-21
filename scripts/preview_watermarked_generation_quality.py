from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watermark_project.config import ECCConfig, GenerationSetting, ModelConfig  # noqa: E402
from watermark_project.ecc_detector import decode_clean_structural_sequence  # noqa: E402
from watermark_project.ecc_generator import EccGenerationResult, EccGenerator, EccRuntimeState  # noqa: E402
from watermark_project.modeling import HfGenerationSession, HfLanguageModel, MockLanguageModel, build_language_model, clean_text  # noqa: E402
from watermark_project.partitioning import build_vocabulary_partition  # noqa: E402

try:  # noqa: E402
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
except Exception:  # pragma: no cover
    torch = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None


DEFAULT_PROMPTS = [
    "Why do people sometimes find it hard to change their mind after seeing new evidence?",
    "How can cities reduce traffic congestion without making daily life harder for residents?",
    "Why does sleep affect memory, mood, and decision-making so strongly?",
    "What makes a scientific explanation trustworthy when experts disagree?",
]

DEFAULT_SYSTEM_PROMPT = (
    "You are a careful explanatory writing assistant. Answer directly without showing reasoning. "
    "Write fluent, self-contained English prose in a neutral factual tone."
)

BAD_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\u007f-\u009f\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


class PreviewSingleGpu4BitHfLanguageModel(HfLanguageModel):
    """HF loader tuned for local quality previews on small single-GPU machines.

    The main project loader intentionally falls back to standard loading if
    4-bit loading fails. For an 8GB GPU and Qwen3-8B, that fallback is more
    harmful than helpful, so this standalone preview script keeps the model on
    GPU 0 in 4-bit and fails loudly instead of trying full precision.
    """

    def _load_model(self, config: ModelConfig, model_kwargs: Dict[str, object], compute_dtype) -> object:
        if config.use_4bit and self.device.startswith("cuda"):
            if AutoModelForCausalLM is None or BitsAndBytesConfig is None or torch is None:
                raise RuntimeError("transformers/torch 4-bit support is unavailable in this environment.")
            quant_kwargs = dict(model_kwargs)
            quant_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
            quant_kwargs["device_map"] = {"": 0}
            quant_kwargs["local_files_only"] = bool(os.environ.get("HF_HUB_OFFLINE") or os.environ.get("TRANSFORMERS_OFFLINE"))
            quant_kwargs.pop("torch_dtype", None)
            quant_kwargs["dtype"] = torch.float16
            model = AutoModelForCausalLM.from_pretrained(config.model_name, **quant_kwargs)
            self._quantization_mode = "4bit"
            print(f"[info] Loaded {config.model_name} with single-GPU 4-bit quantization on {self.device}.")
            return model
        return super()._load_model(config, model_kwargs, compute_dtype)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Standalone preview generator for watermarked text quality. "
            "This script imports watermark components but does not modify or call the main experiment runner."
        )
    )
    parser.add_argument("--backend", choices=["mock", "hf"], default="mock")
    parser.add_argument("--model-name", default="mock-lm")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--use-8bit", action="store_true")
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--partition-prompt-file", default=None)
    parser.add_argument("--output-dir", default="outputs/text_quality_preview")
    parser.add_argument("--num-samples", type=int, default=4)
    parser.add_argument("--prompt-style", choices=["qa", "plain"], default="qa")
    parser.add_argument("--use-chat-template", action="store_true")
    parser.add_argument("--enable-thinking", action="store_true")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--max-prompt-tokens", type=int, default=256)
    parser.add_argument("--target-blocks", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument(
        "--stop-after",
        choices=["closed_blocks", "feasible_blocks"],
        default="closed_blocks",
        help=(
            "Stop ECC preview generation after target_blocks boundary-closed runtime blocks "
            "or after target_blocks VT+Hamming-feasible blocks."
        ),
    )
    parser.add_argument("--watermark-mode", choices=["soft", "hard"], default="soft")
    parser.add_argument("--logit-bias", type=float, default=5.0)
    parser.add_argument("--adaptive", choices=["true", "false"], default="true")
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--sampling", choices=["sample", "greedy"], default="sample")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument("--english-token-filter", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--seed", type=int, default=20260607)
    parser.add_argument("--include-unwatermarked", action="store_true")
    parser.add_argument("--print-samples", type=int, default=4)
    return parser.parse_args()


def load_prompt_lines(path: Optional[str]) -> List[str]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as handle:
        lines = [clean_text(line) for line in handle.readlines()]
    return [line for line in lines if line]


def build_user_prompt(raw_prompt: str, style: str) -> str:
    raw_prompt = clean_text(raw_prompt)
    if style == "plain":
        return raw_prompt
    return (
        "Answer the following question in one coherent paragraph of about 120-180 words. "
        "Do not use bullet points. Keep the tone neutral and factual.\n\n"
        f"Question:\n{raw_prompt}"
    )


def render_prompt_for_model(
    model: Any,
    user_prompt: str,
    system_prompt: str,
    use_chat_template: bool,
    enable_thinking: bool,
) -> Tuple[str, str]:
    if use_chat_template and hasattr(model, "tokenizer") and hasattr(model.tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            rendered = model.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=bool(enable_thinking),
            )
        except TypeError:
            rendered = model.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return rendered, "chat_template"
    if system_prompt:
        rendered = f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        return rendered, "manual_instruction"
    return user_prompt, "raw"


def build_preview_language_model(config: ModelConfig, corpus_texts: Sequence[str]) -> Any:
    if config.backend == "mock":
        return MockLanguageModel(config, corpus_texts=corpus_texts)
    if config.backend == "hf" and config.use_4bit and config.device.lower().startswith("cuda"):
        return PreviewSingleGpu4BitHfLanguageModel(config)
    return build_language_model(config, corpus_texts=corpus_texts)


def start_preview_session(model: Any, rendered_prompt: str, prompt_mode: str):
    if prompt_mode == "chat_template" and hasattr(model, "tokenizer"):
        enc = model.tokenizer(
            rendered_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=model.config.max_prompt_tokens,
            add_special_tokens=False,
        )
        prompt_ids = enc["input_ids"][0].tolist()
        attention_mask = enc["attention_mask"][0].tolist()
        return HfGenerationSession(model, prompt_ids, attention_mask)
    return model.start_session(rendered_prompt)


def apply_repetition_penalty(logits: np.ndarray, generated_ids: Sequence[int], penalty: float) -> np.ndarray:
    if penalty is None or penalty <= 1.0 or not generated_ids:
        return logits
    adjusted = logits.copy()
    for token_id in set(int(x) for x in generated_ids):
        if 0 <= token_id < adjusted.size:
            adjusted[token_id] = adjusted[token_id] / penalty if adjusted[token_id] > 0 else adjusted[token_id] * penalty
    return adjusted


def token_passes_english_filter(model: Any, token_id: int) -> bool:
    if int(token_id) in set(int(x) for x in model.all_special_ids):
        return False
    surface = model.token_surface(int(token_id))
    if not surface:
        return False
    if BAD_TEXT_RE.search(surface):
        return False
    try:
        surface.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


def build_english_ban_mask(model: Any, enabled: bool) -> np.ndarray:
    mask = np.zeros(model.vocab_size, dtype=bool)
    if not enabled:
        return mask
    for token_id in range(model.vocab_size):
        if not token_passes_english_filter(model, token_id):
            mask[token_id] = True
    return mask


def sample_token(
    logits: np.ndarray,
    rng: np.random.Generator,
    sampling: str,
    temperature: float,
    top_k: int,
    top_p: float,
) -> int:
    finite = np.isfinite(logits)
    finite &= logits > -1e8
    if not np.any(finite):
        return int(np.argmax(logits))
    if sampling == "greedy":
        masked = np.where(finite, logits, -1e9)
        return int(np.argmax(masked))

    temp = max(float(temperature), 1e-6)
    scores = np.where(finite, logits / temp, -np.inf)

    if top_k and top_k > 0 and top_k < scores.size:
        keep_ids = np.argpartition(scores, -top_k)[-top_k:]
        keep = np.zeros(scores.size, dtype=bool)
        keep[keep_ids] = True
        scores[~keep] = -np.inf

    valid_ids = np.where(np.isfinite(scores))[0]
    if valid_ids.size == 0:
        return int(np.argmax(logits))
    valid_scores = scores[valid_ids]
    valid_scores = valid_scores - float(np.max(valid_scores))
    probs = np.exp(valid_scores)
    probs = probs / float(np.sum(probs))

    if top_p and 0.0 < top_p < 1.0:
        order = np.argsort(probs)[::-1]
        sorted_probs = probs[order]
        cumulative = np.cumsum(sorted_probs)
        cutoff = int(np.searchsorted(cumulative, top_p, side="left")) + 1
        keep_order = order[: max(1, cutoff)]
        kept_ids = valid_ids[keep_order]
        kept_probs = probs[keep_order]
        kept_probs = kept_probs / float(np.sum(kept_probs))
        return int(rng.choice(kept_ids, p=kept_probs))

    return int(rng.choice(valid_ids, p=probs))


def generate_watermarked_preview(
    generator: EccGenerator,
    raw_prompt: str,
    rendered_prompt: str,
    prompt_mode: str,
    setting: GenerationSetting,
    args: argparse.Namespace,
) -> EccGenerationResult:
    adaptive = bool(setting.adaptive)
    py_rng = random.Random(setting.seed ^ abs(hash(rendered_prompt)))
    np_rng = np.random.default_rng((setting.seed + abs(hash(rendered_prompt))) % (2**32))
    session = start_preview_session(generator.model, rendered_prompt, prompt_mode)
    state = EccRuntimeState()
    generated_ids: List[int] = []
    generated_buckets: List[int] = []
    raw_top_trace: List[Dict[str, Any]] = []
    english_ban_mask = getattr(generator, "preview_english_ban_mask", None)
    steps = 0

    def reached_target() -> bool:
        if args.stop_after == "feasible_blocks":
            return state.completed_blocks >= setting.target_blocks
        return len(state.block_summaries) >= setting.target_blocks

    while not reached_target() and steps < setting.max_new_tokens:
        raw_logits = session.next_logits()
        if not adaptive and state.current_codeword is None and len(state.current_bits) == 0:
            state.current_codeword = generator.choose_fixed_codeword(raw_logits, py_rng)
            state.chosen_codewords.append(state.current_codeword.copy())

        allowed_bits = generator.allowed_next_bits(state.current_bits, adaptive, state.current_codeword)
        if not allowed_bits and len(state.current_bits) < generator.config.block_len:
            allowed_bits = {0, 1}

        if setting.watermark_mode == "hard":
            adjusted_logits = generator.apply_hard_control(
                logits=raw_logits,
                state=state,
                allowed_bits=allowed_bits,
                boundary_bonus=generator.config.boundary_bonus,
            )
        else:
            adjusted_logits = generator.apply_soft_control(
                logits=raw_logits,
                state=state,
                allowed_bits=allowed_bits,
                logit_bias=setting.resolved_logit_bias(),
                boundary_bonus=generator.config.boundary_bonus,
            )

        if english_ban_mask is not None:
            candidate_logits = adjusted_logits.copy()
            candidate_logits[english_ban_mask] = -1e9
            if np.any(np.isfinite(candidate_logits) & (candidate_logits > -1e8)):
                adjusted_logits = candidate_logits
        adjusted_logits = apply_repetition_penalty(adjusted_logits, generated_ids, args.repetition_penalty)
        raw_top_id = int(np.argmax(raw_logits))
        next_id = sample_token(
            adjusted_logits,
            rng=np_rng,
            sampling=args.sampling,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
        )
        next_bucket = int(generator.partition.token_to_bucket[next_id]) if next_id < len(generator.partition.token_to_bucket) else -1
        session.append(next_id)
        generated_ids.append(next_id)
        generated_buckets.append(next_bucket)
        raw_top_trace.append(
            {
                "step": steps,
                "raw_top_id": raw_top_id,
                "chosen_id": next_id,
                "chosen_bucket": next_bucket,
                "payload_len_before_step": len(state.current_bits),
            }
        )
        generator.update_runtime_state(state, next_bucket)
        steps += 1

    full_token_ids = session.prompt_ids + generated_ids
    structural_seq = [bucket for bucket in generated_buckets if bucket in (0, 1, 2)]
    decoded_clean = decode_clean_structural_sequence(structural_seq, generator.codebook)
    return EccGenerationResult(
        prompt=raw_prompt,
        full_text=generator.model.decode(full_token_ids, skip_special_tokens=True),
        suffix_text=generator.model.decode(generated_ids, skip_special_tokens=True),
        generated_token_ids=generated_ids,
        generated_bucket_seq=generated_buckets,
        structural_seq=structural_seq,
        decoded_clean=decoded_clean,
        runtime_state=state,
        raw_top_trace=raw_top_trace,
    )


def generate_unwatermarked_preview(
    model: Any,
    rendered_prompt: str,
    prompt_mode: str,
    args: argparse.Namespace,
    sample_seed: int,
) -> str:
    rng = np.random.default_rng(sample_seed % (2**32))
    session = start_preview_session(model, rendered_prompt, prompt_mode)
    generated_ids: List[int] = []
    special_ids = set(int(x) for x in model.all_special_ids)
    english_ban_mask = build_english_ban_mask(model, args.english_token_filter)
    eos_id = int(model.eos_token_id)
    for _ in range(args.max_new_tokens):
        logits = session.next_logits()
        adjusted = apply_repetition_penalty(logits, generated_ids, args.repetition_penalty)
        for token_id in special_ids:
            if token_id != eos_id and 0 <= token_id < adjusted.size:
                adjusted[token_id] = -1e9
        if args.english_token_filter:
            candidate = adjusted.copy()
            candidate[english_ban_mask] = -1e9
            if np.any(np.isfinite(candidate) & (candidate > -1e8)):
                adjusted = candidate
        next_id = sample_token(adjusted, rng, args.sampling, args.temperature, args.top_k, args.top_p)
        if next_id == eos_id:
            break
        session.append(next_id)
        generated_ids.append(next_id)
    return model.decode(generated_ids, skip_special_tokens=True)


def result_to_row(
    idx: int,
    raw_prompt: str,
    user_prompt: str,
    rendered_prompt: str,
    prompt_mode: str,
    result: EccGenerationResult,
    model: Any,
) -> Dict[str, Any]:
    token_surfaces: List[str] = []
    token_structural_indices: List[Optional[int]] = []
    token_payload_indices: List[Optional[int]] = []
    token_block_ids: List[Optional[int]] = []
    structural_index = 0
    payload_index = 0
    block_len = len(result.runtime_state.block_summaries[0]["bits_prefix_capped"]) if result.runtime_state.block_summaries else 7
    for token_id, bucket in zip(result.generated_token_ids, result.generated_bucket_seq):
        token_surfaces.append(model.token_surface(int(token_id)))
        if int(bucket) in (0, 1, 2):
            token_structural_indices.append(structural_index)
            structural_index += 1
        else:
            token_structural_indices.append(None)
        if int(bucket) in (0, 1):
            token_payload_indices.append(payload_index)
            token_block_ids.append(payload_index // block_len)
            payload_index += 1
        elif int(bucket) == 2:
            boundary_block = max(0, min((payload_index // block_len) - 1, max(0, len(result.runtime_state.block_summaries) - 1)))
            token_payload_indices.append(None)
            token_block_ids.append(boundary_block)
        else:
            token_payload_indices.append(None)
            token_block_ids.append(None)
    return {
        "sample_index": idx,
        "raw_prompt": raw_prompt,
        "user_prompt": user_prompt,
        "prompt_mode": prompt_mode,
        "rendered_prompt": rendered_prompt,
        "watermarked_text": result.suffix_text,
        "full_text": result.full_text,
        "num_generated_tokens": len(result.generated_token_ids),
        "num_structural_symbols": len(result.structural_seq),
        "completed_blocks": result.runtime_state.completed_blocks,
        "runtime_block_summaries": len(result.runtime_state.block_summaries),
        "clean_valid_blocks": result.decoded_clean.get("valid_blocks"),
        "generated_token_ids": json.dumps(result.generated_token_ids),
        "generated_token_surfaces": json.dumps(token_surfaces),
        "generated_bucket_seq": json.dumps(result.generated_bucket_seq),
        "generated_token_structural_indices": json.dumps(token_structural_indices),
        "generated_token_payload_indices": json.dumps(token_payload_indices),
        "generated_token_block_ids": json.dumps(token_block_ids),
        "structural_seq": json.dumps(result.structural_seq),
        "block_summaries": json.dumps(result.runtime_state.block_summaries),
    }


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_lines = load_prompt_lines(args.prompt_file) or DEFAULT_PROMPTS
    prompt_lines = prompt_lines[: max(1, args.num_samples)]
    partition_texts = load_prompt_lines(args.partition_prompt_file) if args.partition_prompt_file else prompt_lines
    if not partition_texts:
        partition_texts = prompt_lines

    model_config = ModelConfig(
        backend=args.backend,
        model_name=args.model_name,
        device=args.device,
        max_prompt_tokens=args.max_prompt_tokens,
        mock_vocab_size=256,
        use_4bit=args.use_4bit,
        use_8bit=args.use_8bit,
    )
    model = build_preview_language_model(model_config, corpus_texts=partition_texts)
    ecc_config = ECCConfig(block_len=args.block_len, vt_a=args.vt_a)
    partition = build_vocabulary_partition(model, partition_texts, ecc_config)
    generator = EccGenerator(model, partition, ecc_config)
    generator.preview_english_ban_mask = build_english_ban_mask(model, args.english_token_filter)

    setting = GenerationSetting(
        scheme="ecc",
        watermark_mode=args.watermark_mode,
        adaptive=(args.adaptive.lower() == "true"),
        target_blocks=args.target_blocks,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
        logit_bias=args.logit_bias,
    )

    rows: List[Dict[str, Any]] = []
    detailed: List[Dict[str, Any]] = []
    for idx, raw_prompt in enumerate(prompt_lines):
        user_prompt = build_user_prompt(raw_prompt, args.prompt_style)
        rendered_prompt, prompt_mode = render_prompt_for_model(
            model=model,
            user_prompt=user_prompt,
            system_prompt=args.system_prompt,
            use_chat_template=args.use_chat_template,
            enable_thinking=args.enable_thinking,
        )
        wm_result = generate_watermarked_preview(generator, raw_prompt, rendered_prompt, prompt_mode, setting, args)
        row = result_to_row(idx, raw_prompt, user_prompt, rendered_prompt, prompt_mode, wm_result, model)
        if args.include_unwatermarked:
            row["unwatermarked_text"] = generate_unwatermarked_preview(
                model=model,
                rendered_prompt=rendered_prompt,
                prompt_mode=prompt_mode,
                args=args,
                sample_seed=args.seed + 9000 + idx,
            )
        rows.append(row)
        detailed.append(
            {
                **row,
                "generated_token_ids": wm_result.generated_token_ids,
                "raw_top_trace": wm_result.raw_top_trace,
                "decoded_clean": wm_result.decoded_clean,
                "setting": asdict(setting),
            }
        )

    csv_path = output_dir / "preview_generations.csv"
    json_path = output_dir / "preview_generations.json"
    config_path = output_dir / "preview_config.json"

    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(detailed, handle, ensure_ascii=False, indent=2)
    with open(config_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "args": vars(args),
                "model_device": getattr(model, "resolved_device", args.device),
                "quantization_mode": getattr(model, "quantization_mode", "none"),
                "num_partition_texts": len(partition_texts),
                "partition_prompt_file": args.partition_prompt_file,
                "partition_source": "partition_prompt_file" if args.partition_prompt_file else "preview_prompts",
                "num_bucket0": len(partition.bucket0_ids),
                "num_bucket1": len(partition.bucket1_ids),
                "num_boundary": len(partition.boundary_ids),
                "english_token_filter": bool(args.english_token_filter),
                "stop_after": args.stop_after,
                "num_english_filter_banned": int(np.sum(generator.preview_english_ban_mask)),
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved preview CSV: {csv_path}")
    print(f"Saved preview JSON: {json_path}")
    print(f"Saved config: {config_path}")
    for row in rows[: max(0, args.print_samples)]:
        print("\n" + "=" * 80)
        print(f"sample_index={row['sample_index']} prompt_mode={row['prompt_mode']}")
        print(f"prompt: {row['raw_prompt']}")
        print("- watermarked:")
        print(row["watermarked_text"])
        if args.include_unwatermarked:
            print("- unwatermarked:")
            print(row["unwatermarked_text"])
        print(
            "blocks="
            f"{row['completed_blocks']} clean_valid={row['clean_valid_blocks']} "
            f"tokens={row['num_generated_tokens']}"
        )


if __name__ == "__main__":
    main()
