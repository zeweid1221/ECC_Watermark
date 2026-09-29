from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baselines.combinatorial_watermark import (  # noqa: E402
    CombinatorialConfig,
    CombinatorialGenerationResult,
    CombinatorialWatermark,
    calibrate_lower_tail_threshold,
    calibrate_strict_lower_tail_threshold,
    clean_block_min_scores,
    complete_mismatch_threshold,
    evaluate_combinatorial_blocks,
)
from watermark_project.config import (  # noqa: E402
    GenerationProtocolConfig,
    ModelConfig,
    PromptConfig,
)
from watermark_project.edits import apply_token_edits_to_blocks  # noqa: E402
from watermark_project.io_utils import ensure_dir, save_dataframe, save_prompts, write_json  # noqa: E402
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile  # noqa: E402
from watermark_project.modeling import build_language_model, sample_prompts_from_config  # noqa: E402
from watermark_project.ppl import compute_generation_perplexities  # noqa: E402


def parse_csv(value: str, cast):
    return [cast(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independent combinatorial-watermark generation and edit-detection baseline."
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
    parser.add_argument("--patterns", default="AB,ACADBCBD")
    parser.add_argument("--logit-bias-values", default="2,5,20,50")
    parser.add_argument("--watermark-key", type=int, default=3779)
    parser.add_argument("--target-blocks", type=int, default=18)
    parser.add_argument("--evaluation-block-len", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--edit-rates", default="0.2,0.4,0.6,0.8")
    parser.add_argument("--attack-max-edits-per-blocks", default="1,2,3")
    parser.add_argument(
        "--edit-count-mode",
        choices=["uniform_1_to_k", "fixed_k"],
        default="uniform_1_to_k",
    )
    parser.add_argument("--target-clean-far", type=float, default=0.1)
    parser.add_argument(
        "--threshold-mode",
        choices=[
            "fixed_complete_mismatch",
            "clean_type_i_0.1",
            "original_token",
            "legacy_separate_block",
        ],
        default="fixed_complete_mismatch",
        help=(
            "fixed_complete_mismatch uses one bias-independent threshold per pattern; "
            "clean_type_i_0.1 calibrates token Type-I error on clean outputs; "
            "original_token is retained as an alias for that calibration; "
            "legacy_separate_block retains the earlier adapted calibration."
        ),
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
    args.patterns = parse_csv(args.patterns, str)
    args.logit_bias_values = parse_csv(args.logit_bias_values, float)
    args.edit_rates = parse_csv(args.edit_rates, float)
    args.attack_max_edits_per_blocks = parse_csv(
        args.attack_max_edits_per_blocks,
        int,
    )
    if not args.patterns or not args.logit_bias_values:
        parser.error("--patterns and --logit-bias-values must not be empty.")
    return args


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _aggregate_counts(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {
        key: int(sum(int(row[key]) for row in rows))
        for key in ("TP", "FP", "FN", "TN", "token_tp", "token_fp", "token_fn", "token_tn")
    }
    token_precision = _safe_div(totals["token_tp"], totals["token_tp"] + totals["token_fp"])
    token_recall = _safe_div(totals["token_tp"], totals["token_tp"] + totals["token_fn"])
    return {
        **totals,
        "block_tpr": _safe_div(totals["TP"], totals["TP"] + totals["FN"]),
        "block_far": _safe_div(totals["FP"], totals["FP"] + totals["TN"]),
        "token_precision": token_precision,
        "token_recall": token_recall,
        "token_f1": _safe_div(
            2.0 * token_precision * token_recall,
            token_precision + token_recall,
        ),
        "token_far": _safe_div(
            totals["token_fp"],
            totals["token_fp"] + totals["token_tn"],
        ),
    }


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


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
        raise RuntimeError(
            f"Requested {args.num_samples} prompts but loaded {len(prompts)}."
        )
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

    summary_rows: List[Dict[str, Any]] = []
    detail_rows: List[Dict[str, Any]] = []
    generated_payload: List[Dict[str, Any]] = []
    special_ids = set(int(x) for x in model.all_special_ids)
    attack_vocab_ids = [
        token_id for token_id in range(model.vocab_size) if token_id not in special_ids
    ]

    for pattern_name in args.patterns:
        config = CombinatorialConfig(
            pattern_name=pattern_name,
            watermark_key=args.watermark_key,
            evaluation_block_len=args.evaluation_block_len,
            target_clean_far=args.target_clean_far,
        )
        method = CombinatorialWatermark(model, config, protocol)
        for logit_bias in args.logit_bias_values:
            generated: List[CombinatorialGenerationResult] = []
            clean_scores: List[Dict[str, Any]] = []
            for sequence_index, prompt in enumerate(prompts):
                result = method.generate_one(
                    prompt,
                    logit_bias=logit_bias,
                    target_blocks=args.target_blocks,
                    max_new_tokens=args.max_new_tokens,
                    seed=args.generation_seed + sequence_index,
                )
                generated.append(result)
                score = method.score_tokens(
                    result.generated_token_ids,
                    result.prompt_token_ids[-1],
                )
                clean_scores.append(score)

            flattened_clean_scores = [
                value
                for score in clean_scores
                for value in score["local_scores"]
            ]
            if args.threshold_mode == "fixed_complete_mismatch":
                token_threshold = complete_mismatch_threshold(config.pattern_name)
                block_threshold = token_threshold
                clean_token_alarm_rate = float(
                    np.mean(
                        np.asarray(flattened_clean_scores, dtype=np.float64)
                        < token_threshold
                    )
                )
                threshold_source = "fixed_complete_local_mismatch"
                block_decision_rule = "any_original_token_alarm_in_block"
                separate_block_threshold_calibrated = False
            elif args.threshold_mode in {"clean_type_i_0.1", "original_token"}:
                token_threshold = calibrate_strict_lower_tail_threshold(
                    flattened_clean_scores,
                    args.target_clean_far,
                )
                # Compatibility alias only; no separate block threshold is calibrated.
                block_threshold = token_threshold
                clean_token_alarm_rate = float(
                    np.mean(
                        np.asarray(flattened_clean_scores, dtype=np.float64)
                        < token_threshold
                    )
                )
                threshold_source = "clean_type_i_0.1"
                block_decision_rule = "any_original_token_alarm_in_block"
                separate_block_threshold_calibrated = False
            else:
                token_threshold = calibrate_lower_tail_threshold(
                    flattened_clean_scores,
                    args.target_clean_far,
                )
                block_threshold = calibrate_lower_tail_threshold(
                    [
                        value
                        for score in clean_scores
                        for value in clean_block_min_scores(
                            score["local_scores"],
                            args.evaluation_block_len,
                        )
                    ],
                    args.target_clean_far,
                )
                clean_token_alarm_rate = float(
                    np.mean(
                        np.asarray(flattened_clean_scores, dtype=np.float64)
                        <= token_threshold
                    )
                )
                threshold_source = "legacy_separate_token_and_block_calibration"
                block_decision_rule = "separate_block_min_score_threshold"
                separate_block_threshold_calibrated = True
            ppl = compute_generation_perplexities(
                model,
                [result.prompt_token_ids for result in generated],
                [result.generated_token_ids for result in generated],
            )
            setting_key = f"combinatorial_{config.pattern_name.lower()}_bias{logit_bias:g}"
            for sequence_index, (result, score) in enumerate(zip(generated, clean_scores)):
                generated_payload.append(
                    {
                        "setting_key": setting_key,
                        "sequence_index": sequence_index,
                        "pattern": config.pattern_name,
                        "num_buckets": config.num_colors,
                        "logit_bias": logit_bias,
                        "prompt": result.prompt,
                        "rendered_prompt": result.rendered_prompt,
                        "prompt_mode": result.prompt_mode,
                        "prompt_token_ids": result.prompt_token_ids,
                        "suffix_text": result.suffix_text,
                        "generated_token_ids": result.generated_token_ids,
                        "generated_colors": result.generated_colors,
                        "target_colors": result.target_colors,
                        "pattern_adherence": result.pattern_adherence,
                        "global_score": score["global_score"],
                        "clean_local_scores": score["local_scores"],
                        "raw_top_trace": result.raw_top_trace,
                    }
                )

            for attack_budget in args.attack_max_edits_per_blocks:
                for edit_rate in args.edit_rates:
                    setting_details: List[Dict[str, Any]] = []
                    for sequence_index, result in enumerate(generated):
                        attacked = apply_token_edits_to_blocks(
                            token_blocks=[list(block) for block in result.block_tokens],
                            edit_rate=edit_rate,
                            max_edits_per_block=attack_budget,
                            edit_count_mode=args.edit_count_mode,
                            vocab_ids=attack_vocab_ids,
                            rng=random.Random(
                                args.generation_seed
                                + sequence_index
                                + int(edit_rate * 1000)
                                + 10000 * attack_budget
                                + 100000 * config.num_colors
                            ),
                        )
                        observed_sequence = attacked["observed_full_sequence"]
                        observed_score = method.score_tokens(
                            observed_sequence,
                            result.prompt_token_ids[-1],
                        )
                        evaluation = evaluate_combinatorial_blocks(
                            result.block_tokens,
                            attacked["observed_blocks"],
                            attacked["origin_maps_per_block"],
                            attacked["gt_events_per_block"],
                            observed_score["local_scores"],
                            token_threshold=token_threshold,
                            block_threshold=block_threshold,
                            threshold_mode=args.threshold_mode,
                        )
                        row = {
                            "setting_key": setting_key,
                            "sequence_index": sequence_index,
                            "scheme": "combinatorial_watermark",
                            "pattern": config.pattern_name,
                            "num_buckets": config.num_colors,
                            "logit_bias": logit_bias,
                            "adaptive": False,
                            "edit_rate": edit_rate,
                            "attack_max_edits_per_block": attack_budget,
                            "edit_count_mode": args.edit_count_mode,
                            "num_blocks": len(result.block_tokens),
                            "token_threshold": token_threshold,
                            "block_threshold": block_threshold,
                            "canonical_original_token_threshold": (
                                token_threshold
                                if args.threshold_mode != "legacy_separate_block"
                                else None
                            ),
                            "clean_token_alarm_rate": clean_token_alarm_rate,
                            "threshold_mode": args.threshold_mode,
                            "threshold_source": threshold_source,
                            "block_decision_rule": block_decision_rule,
                            "separate_block_threshold_calibrated": (
                                separate_block_threshold_calibrated
                            ),
                            "pattern_adherence": result.pattern_adherence,
                            "clean_global_score": clean_scores[sequence_index]["global_score"],
                            "observed_global_score": observed_score["global_score"],
                            "pred_blocks": _json(evaluation["pred_blocks"]),
                            "gt_blocks": _json(evaluation["gt_blocks"]),
                            "block_scores": _json(evaluation["block_scores"]),
                            **{
                                key: evaluation[key]
                                for key in (
                                    "TP",
                                    "FP",
                                    "FN",
                                    "TN",
                                    "block_tpr",
                                    "block_far",
                                    "token_tp",
                                    "token_fp",
                                    "token_fn",
                                    "token_tn",
                                    "token_precision",
                                    "token_recall",
                                    "token_f1",
                                    "token_far",
                                )
                            },
                        }
                        setting_details.append(row)
                        detail_rows.append(row)

                    aggregate = _aggregate_counts(setting_details)
                    summary_rows.append(
                        {
                            "setting_key": setting_key,
                            "scheme": "combinatorial_watermark",
                            "pattern": config.pattern_name,
                            "num_buckets": config.num_colors,
                            "logit_bias": logit_bias,
                            "adaptive": False,
                            "edit_rate": edit_rate,
                            "attack_max_edits_per_block": attack_budget,
                            "edit_count_mode": args.edit_count_mode,
                            "num_sequences_total": len(generated),
                            "num_sequences_used": len(generated),
                            "mean_valid_blocks_per_used_sequence": float(
                                np.mean([len(result.block_tokens) for result in generated])
                            ),
                            "target_clean_far": args.target_clean_far,
                            "token_threshold": token_threshold,
                            "block_threshold": block_threshold,
                            "canonical_original_token_threshold": (
                                token_threshold
                                if args.threshold_mode != "legacy_separate_block"
                                else None
                            ),
                            "clean_token_alarm_rate": clean_token_alarm_rate,
                            "threshold_mode": args.threshold_mode,
                            "threshold_source": threshold_source,
                            "block_decision_rule": block_decision_rule,
                            "separate_block_threshold_calibrated": (
                                separate_block_threshold_calibrated
                            ),
                            "mean_pattern_adherence": float(
                                np.mean([result.pattern_adherence for result in generated])
                            ),
                            "mean_clean_global_score": float(
                                np.mean([score["global_score"] for score in clean_scores])
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
    write_json(
        str(Path(args.output_dir) / "generated.json"),
        generated_payload,
    )
    write_json(
        str(Path(args.output_dir) / "config.json"),
        {
            "args": vars(args),
            "protocol": asdict(protocol),
            "model_device": getattr(model, "resolved_device", args.device),
            "quantization_mode": getattr(model, "quantization_mode", "none"),
            "partition_definition": (
                "Every vocabulary token is assigned to exactly one context-dependent "
                "pseudorandom bucket using (watermark_key, previous_token_id, token_id)."
            ),
            "calibration_note": (
                "The default fixed_complete_mismatch mode uses tau_e = 1/w for every "
                "logit bias, so a token alarm requires zero matching checks in its local "
                "window. The clean_type_i_0.1 mode instead calibrates tau_e on clean scores "
                "to control token-level Type-I error. Both modes map token alarms to blocks "
                "by union and never use attack labels. The optional legacy_separate_block "
                "mode reproduces the earlier adapted block calibration."
            ),
        },
    )
    print(f"Saved {len(summary_df)} summary rows to {Path(args.output_dir) / 'summary.csv'}")
    print(f"Saved {len(details_df)} detail rows to {Path(args.output_dir) / 'details.csv'}")


if __name__ == "__main__":
    main()
