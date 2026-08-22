"""Run the accepted synchronization-string plus VT baseline on LFQA prompts."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import random
from pathlib import Path
import sys
from typing import Any, Dict, List

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baselines.sync_ecc import (  # noqa: E402
    SyncEccConfig,
    SyncEccGenerationResult,
    SyncEccWatermark,
    aggregate_sync_rows,
    apply_sync_attacks,
    evaluate_sync_blocks,
)
from watermark_project.config import GenerationProtocolConfig, ModelConfig, PromptConfig  # noqa: E402
from watermark_project.io_utils import ensure_dir, save_dataframe, save_prompts, write_json  # noqa: E402
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile  # noqa: E402
from watermark_project.modeling import build_language_model, sample_prompts_from_config  # noqa: E402
from watermark_project.ppl import compute_generation_perplexities  # noqa: E402


def parse_csv(value: str, cast):
    return [cast(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reproduce the accepted synchronization-string plus VT construction "
            "under the ECC-IW LFQA generation and attack protocol."
        )
    )
    parser.add_argument("--backend", choices=["mock", "hf"], default="mock")
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default=None)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--use-8bit", action="store_true")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--num-samples", type=int, default=256)
    parser.add_argument("--min-prompt-chars", type=int, default=64)
    parser.add_argument("--prompt-seed", type=int, default=1234)
    parser.add_argument("--generation-seed", type=int, default=2026)
    parser.add_argument("--watermark-seed", type=int, default=19920408)
    parser.add_argument("--logit-bias-values", default="2,5,20")
    parser.add_argument("--watermark-mode", choices=["soft", "hard"], default="soft")
    parser.add_argument("--target-blocks", type=int, default=18)
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--sigma-size", type=int, default=4)
    parser.add_argument("--vt-a", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--edit-rates", default="0.2,0.4,0.6,0.8")
    parser.add_argument("--attack-max-edits-per-blocks", default="1,2,3")
    parser.add_argument("--attack-types", default="insert,delete,substitute")
    parser.add_argument(
        "--edit-count-mode",
        choices=["uniform_1_to_k", "fixed_k"],
        default="uniform_1_to_k",
    )
    parser.add_argument("--candidate-tolerance", type=int, default=1)
    parser.add_argument(
        "--strict-interior-insertions",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--sampling", choices=["sample", "greedy"], default="sample")
    parser.add_argument("--temperature", type=float, default=0.75)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.2)
    parser.add_argument("--prompt-style", choices=["qa", "plain"], default="qa")
    parser.add_argument(
        "--use-chat-template",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument("--enable-thinking", action="store_true")
    parser.add_argument(
        "--system-prompt",
        default=(
            "You are a careful explanatory writing assistant. Answer directly without showing reasoning. "
            "Write fluent, self-contained English prose in a neutral factual tone."
        ),
    )
    parser.add_argument(
        "--english-token-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--save-parquet", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    profile = get_model_profile(args.model_profile) if args.model_profile else None
    if profile and args.model_name and args.model_name != profile.model_name:
        parser.error(
            f"--model-profile {profile.key} requires --model-name {profile.model_name!r}."
        )
    args.model_name = args.model_name or (profile.model_name if profile else "mock-lm")
    if args.use_chat_template is None:
        args.use_chat_template = profile.use_chat_template if profile else False
    args.logit_bias_values = parse_csv(args.logit_bias_values, float)
    args.edit_rates = parse_csv(args.edit_rates, float)
    args.attack_max_edits_per_blocks = parse_csv(args.attack_max_edits_per_blocks, int)
    args.attack_types = parse_csv(args.attack_types, str)
    if not args.logit_bias_values:
        parser.error("--logit-bias-values must not be empty.")
    if not args.attack_types:
        parser.error("--attack-types must not be empty.")
    invalid_attacks = set(args.attack_types) - {"insert", "delete", "substitute"}
    if invalid_attacks:
        parser.error(f"Unknown attack types: {sorted(invalid_attacks)}")
    if args.max_new_tokens < args.target_blocks * args.block_len:
        parser.error("--max-new-tokens cannot fit the requested number of complete VT blocks.")
    return args


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _generation_record(
    result: SyncEccGenerationResult,
    *,
    setting_key: str,
    sequence_index: int,
    logit_bias: float,
    watermark_mode: str,
    clean_detection,
) -> Dict[str, Any]:
    return {
        "setting_key": setting_key,
        "sequence_index": int(sequence_index),
        "scheme": "sync_ecc_accepted",
        "logit_bias": float(logit_bias),
        "watermark_mode": watermark_mode,
        "prompt": result.prompt,
        "user_prompt": result.user_prompt,
        "rendered_prompt": result.rendered_prompt,
        "prompt_mode": result.prompt_mode,
        "prompt_token_ids": result.prompt_token_ids,
        "suffix_text": result.suffix_text,
        "generated_token_ids": result.generated_token_ids,
        "target_codewords": result.target_codewords,
        "target_bits": result.target_bits,
        "target_sync_symbols": result.target_sync_symbols,
        "target_step_buckets": result.target_step_buckets,
        "observed_bits": result.observed_bits,
        "observed_sync_symbols": result.observed_sync_symbols,
        "observed_step_buckets": result.observed_step_buckets,
        "tag_adherence": result.tag_adherence,
        "sync_adherence": result.sync_adherence,
        "bit_adherence": result.bit_adherence,
        "clean_vt_valid_rate": result.clean_vt_valid_rate,
        "clean_alignment_distance": clean_detection.alignment.distance,
        "clean_predicted_blocks": clean_detection.predicted_blocks,
        "clean_block_distances": clean_detection.block_distances,
    }


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    prompts = sample_prompts_from_config(
        PromptConfig(
            prompt_text_file=args.prompt_file,
            prompt_count=args.num_samples,
            min_prompt_chars=args.min_prompt_chars,
            prompt_seed=args.prompt_seed,
        ),
        random.Random(args.prompt_seed),
    )
    if len(prompts) != args.num_samples:
        raise RuntimeError(f"Requested {args.num_samples} prompts but loaded {len(prompts)}.")
    save_prompts(str(Path(args.output_dir) / "prompts.txt"), prompts)

    model = build_language_model(
        ModelConfig(
            backend=args.backend,
            model_name=args.model_name,
            model_profile=args.model_profile,
            device=args.device,
            max_prompt_tokens=256,
            mock_vocab_size=256,
            use_4bit=args.use_4bit,
            use_8bit=args.use_8bit,
        ),
        corpus_texts=prompts,
    )
    protocol = GenerationProtocolConfig(
        stop_after="closed_blocks",
        sampling=args.sampling,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        prompt_style=args.prompt_style,
        use_chat_template=bool(args.use_chat_template),
        enable_thinking=bool(args.enable_thinking),
        system_prompt=args.system_prompt,
        ascii_token_filter=bool(args.english_token_filter),
    )
    sync_config = SyncEccConfig(
        block_len=args.block_len,
        sigma_size=args.sigma_size,
        vt_a=args.vt_a,
        seed=args.watermark_seed,
    )
    method = SyncEccWatermark(model, sync_config, protocol)
    codewords_by_sequence = method.schedule.sample_codewords(
        len(prompts),
        args.target_blocks,
    )
    special_ids = set(int(value) for value in model.all_special_ids)
    attack_vocab_ids = [
        token_id
        for token_id in range(model.vocab_size)
        if token_id not in special_ids and not method.ban_mask[token_id]
    ]

    summary_rows: List[Dict[str, Any]] = []
    detail_rows: List[Dict[str, Any]] = []
    generated_rows: List[Dict[str, Any]] = []
    hard = args.watermark_mode == "hard"
    for logit_bias in args.logit_bias_values:
        generated: List[SyncEccGenerationResult] = []
        clean_detections = []
        for sequence_index, prompt in enumerate(prompts):
            result = method.generate_one(
                prompt,
                codewords=codewords_by_sequence[sequence_index],
                logit_bias=logit_bias,
                hard=hard,
                max_new_tokens=args.max_new_tokens,
                seed=args.generation_seed + sequence_index,
            )
            clean_detection = method.detect(result.generated_token_ids, args.target_blocks)
            generated.append(result)
            clean_detections.append(clean_detection)
            setting_key = f"sync_ecc_{args.watermark_mode}_bias{logit_bias:g}"
            generated_rows.append(
                _generation_record(
                    result,
                    setting_key=setting_key,
                    sequence_index=sequence_index,
                    logit_bias=logit_bias,
                    watermark_mode=args.watermark_mode,
                    clean_detection=clean_detection,
                )
            )

        ppl = compute_generation_perplexities(
            model,
            [result.prompt_token_ids for result in generated],
            [result.generated_token_ids for result in generated],
            generated_texts=[result.suffix_text for result in generated],
        )
        setting_key = f"sync_ecc_{args.watermark_mode}_bias{logit_bias:g}"
        for attack_type in args.attack_types:
            for attack_budget in args.attack_max_edits_per_blocks:
                for edit_rate in args.edit_rates:
                    setting_details: List[Dict[str, Any]] = []
                    for sequence_index, result in enumerate(generated):
                        attacked = apply_sync_attacks(
                            result.block_tokens,
                            edit_rate=edit_rate,
                            max_edits_per_block=attack_budget,
                            edit_count_mode=args.edit_count_mode,
                            attack_type=attack_type,
                            vocab_ids=attack_vocab_ids,
                            schedule=method.schedule,
                            rng=random.Random(
                                args.generation_seed
                                + sequence_index
                                + int(edit_rate * 1000)
                                + 10000 * attack_budget
                                + 100000 * (args.attack_types.index(attack_type) + 1)
                            ),
                            strict_interior_insertions=args.strict_interior_insertions,
                        )
                        detection = method.detect(attacked.observed_token_ids, args.target_blocks)
                        evaluation = evaluate_sync_blocks(
                            detection,
                            attacked.gt_events_per_block,
                            args.target_blocks,
                            candidate_tolerance=args.candidate_tolerance,
                        )
                        row = {
                            "setting_key": setting_key,
                            "sequence_index": int(sequence_index),
                            "scheme": "sync_ecc_accepted",
                            "model_profile": args.model_profile,
                            "logit_bias": float(logit_bias),
                            "watermark_mode": args.watermark_mode,
                            "block_len": args.block_len,
                            "sigma_size": args.sigma_size,
                            "vt_a": args.vt_a,
                            "edit_rate": float(edit_rate),
                            "attack_type": attack_type,
                            "attack_max_edits_per_block": int(attack_budget),
                            "edit_count_mode": args.edit_count_mode,
                            "num_blocks": args.target_blocks,
                            "realized_edits": attacked.realized_edits,
                            "tag_adherence": result.tag_adherence,
                            "clean_vt_valid_rate": result.clean_vt_valid_rate,
                            "clean_predicted_blocks": _json(
                                clean_detections[sequence_index].predicted_blocks
                            ),
                            "alignment_distance": detection.alignment.distance,
                            "alignment_blocks": _json(detection.alignment_blocks),
                            "vt_inconsistent_blocks": _json(detection.vt_inconsistent_blocks),
                            "candidate_positions": _json(detection.candidate_positions),
                            "candidate_events_by_block": _json(
                                detection.candidate_events_by_block
                            ),
                            "gt_blocks": _json(evaluation["gt_blocks"]),
                            "pred_blocks": _json(evaluation["pred_blocks"]),
                            **{
                                key: evaluation[key]
                                for key in (
                                    "TP",
                                    "FP",
                                    "FN",
                                    "TN",
                                    "block_tpr",
                                    "block_far",
                                    "candidate_events",
                                    "candidate_events_covered",
                                    "candidate_coverage",
                                    "candidate_nonempty_sets",
                                    "candidate_total_size",
                                    "mean_candidate_set_size",
                                )
                            },
                        }
                        setting_details.append(row)
                        detail_rows.append(row)

                    aggregate = aggregate_sync_rows(setting_details)
                    summary_rows.append(
                        {
                            "setting_key": setting_key,
                            "scheme": "sync_ecc_accepted",
                            "model_profile": args.model_profile,
                            "logit_bias": float(logit_bias),
                            "watermark_mode": args.watermark_mode,
                            "block_len": args.block_len,
                            "sigma_size": args.sigma_size,
                            "vt_a": args.vt_a,
                            "edit_rate": float(edit_rate),
                            "attack_type": attack_type,
                            "attack_max_edits_per_block": int(attack_budget),
                            "edit_count_mode": args.edit_count_mode,
                            "num_sequences_total": len(generated),
                            "num_sequences_used": len(generated),
                            "target_blocks": args.target_blocks,
                            "mean_realized_edits": float(
                                np.mean([row["realized_edits"] for row in setting_details])
                            ),
                            "mean_tag_adherence": float(
                                np.mean([result.tag_adherence for result in generated])
                            ),
                            "mean_sync_adherence": float(
                                np.mean([result.sync_adherence for result in generated])
                            ),
                            "mean_bit_adherence": float(
                                np.mean([result.bit_adherence for result in generated])
                            ),
                            "mean_clean_vt_valid_rate": float(
                                np.mean([result.clean_vt_valid_rate for result in generated])
                            ),
                            "mean_clean_flagged_blocks": float(
                                np.mean(
                                    [len(detection.predicted_blocks) for detection in clean_detections]
                                )
                            ),
                            **ppl,
                            **aggregate,
                        }
                    )

    summary_df = pd.DataFrame(summary_rows)
    details_df = pd.DataFrame(detail_rows)
    save_dataframe(
        summary_df,
        str(Path(args.output_dir) / "summary"),
        save_parquet=args.save_parquet,
    )
    save_dataframe(
        details_df,
        str(Path(args.output_dir) / "details"),
        save_parquet=args.save_parquet,
    )
    write_json(str(Path(args.output_dir) / "generated.json"), generated_rows)
    bucket_counts = np.bincount(
        method.schedule.base_bucket_ids.astype(np.int64),
        minlength=sync_config.bucket_count,
    ).tolist()
    write_json(
        str(Path(args.output_dir) / "config.json"),
        {
            "args": vars(args),
            "protocol": asdict(protocol),
            "sync_ecc_config": asdict(sync_config),
            "resolved_seeds": {
                "bucket": sync_config.resolved_seed_bucket,
                "sync": sync_config.resolved_seed_sync,
                "message": sync_config.resolved_seed_message,
            },
            "base_bucket_counts": bucket_counts,
            "model_device": getattr(model, "resolved_device", args.device),
            "quantization_mode": getattr(model, "quantization_mode", "none"),
            "method_provenance": (
                "Readable reimplementation of the synchronization-string plus VT "
                "construction accepted to Findings of EMNLP 2026. It is isolated from "
                "the current ECC-IW implementation and uses the shared LFQA evaluator."
            ),
            "attack_note": (
                "Insertion and deletion are native sync-ECC attacks. Substitution is an "
                "out-of-scope stress test and is sampled to change the induced step bucket."
            ),
        },
    )
    print(f"Saved {len(summary_df)} summary rows to {Path(args.output_dir) / 'summary.csv'}")
    print(f"Saved {len(details_df)} detail rows to {Path(args.output_dir) / 'details.csv'}")


if __name__ == "__main__":
    main()
