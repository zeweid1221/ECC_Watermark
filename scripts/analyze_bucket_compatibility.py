from __future__ import annotations

import argparse
import gc
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watermark_project.bucket_compatibility import (  # noqa: E402
    reconstruct_admissible_steps,
    soft_intervention_kl_nats,
)
from watermark_project.ecc_detector import EccCodebook  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure native LM probability mass assigned to ECC-admissible buckets."
    )
    parser.add_argument("--detailed-results", required=True)
    parser.add_argument("--partition-dir", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-profile", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use-4bit", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--local-files-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--setting-keys", default=None, help="Optional comma-separated setting keys.")
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--checkpoint-every", type=int, default=16)
    parser.add_argument("--ppl-summary-csv", default=None)
    parser.add_argument(
        "--invalid-prefix-policy",
        choices=["nearest_feasible", "legacy_unconstrained"],
        default="legacy_unconstrained",
        help=(
            "Use legacy_unconstrained for existing archives generated before prefix recovery; "
            "use nearest_feasible for newly generated outputs that record that policy."
        ),
    )
    return parser.parse_args()


def load_model(args: argparse.Namespace):
    kwargs: Dict[str, Any] = {
        "local_files_only": bool(args.local_files_only),
        "low_cpu_mem_usage": True,
    }
    if args.device.startswith("cuda") and args.use_4bit:
        compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        kwargs.update(
            {
                "quantization_config": BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=compute_dtype,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                ),
                "device_map": {"": 0},
            }
        )
    else:
        kwargs["dtype"] = torch.float16 if args.device.startswith("cuda") else torch.float32
    model = AutoModelForCausalLM.from_pretrained(args.model_name, **kwargs)
    if not (args.device.startswith("cuda") and args.use_4bit):
        model.to(args.device)
    model.eval()
    model.config.use_cache = False
    return model


def model_device(model) -> torch.device:
    return next(model.parameters()).device


def log_bucket_masses(
    logits: torch.Tensor,
    bucket_indices: Dict[int, torch.Tensor],
) -> Dict[int, torch.Tensor]:
    log_normalizer = torch.logsumexp(logits, dim=-1)
    return {
        bucket: torch.logsumexp(logits.index_select(-1, indices), dim=-1) - log_normalizer
        for bucket, indices in bucket_indices.items()
    }


def safe_spearman(left: Sequence[float], right: Sequence[float]) -> float:
    left_values = np.asarray(left, dtype=float)
    right_values = np.asarray(right, dtype=float)
    finite = np.isfinite(left_values) & np.isfinite(right_values)
    left_values = left_values[finite]
    right_values = right_values[finite]
    if (
        len(left_values) < 3
        or len(np.unique(left_values)) < 2
        or len(np.unique(right_values)) < 2
    ):
        return math.nan
    left_ranks = pd.Series(left_values).rank(method="average").to_numpy()
    right_ranks = pd.Series(right_values).rank(method="average").to_numpy()
    return float(np.corrcoef(left_ranks, right_ranks)[0, 1])


def save_frames(
    output_dir: Path,
    step_rows: List[Dict[str, Any]],
    sequence_rows: List[Dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    step_frame = pd.DataFrame(step_rows)
    sequence_frame = pd.DataFrame(sequence_rows)
    step_frame.to_parquet(output_dir / "bucket_compatibility_steps.parquet", index=False)
    sequence_frame.to_csv(output_dir / "bucket_compatibility_sequences.csv", index=False)


def summarize(
    step_frame: pd.DataFrame,
    sequence_frame: pd.DataFrame,
    source_settings: Sequence[Dict[str, Any]],
    args: argparse.Namespace,
) -> pd.DataFrame:
    source_ppl = {
        str(setting["setting_key"]): float(setting.get("ppl_conditional_token_ids", math.nan))
        for setting in source_settings
    }
    clean_ppl = math.nan
    if args.ppl_summary_csv:
        ppl = pd.read_csv(args.ppl_summary_csv)
        clean = ppl[
            (ppl["model_profile"] == args.model_profile)
            & (ppl["setting_type"] == "unwatermarked")
        ]
        if not clean.empty:
            clean_ppl = float(clean.iloc[0]["ppl_conditional_token_ids"])

    records: List[Dict[str, Any]] = []
    for setting_key, group in step_frame.groupby("setting_key", sort=False):
        seq_group = sequence_frame[sequence_frame["setting_key"] == setting_key]
        total_nll = float(group["chosen_token_nll"].sum())
        total_steps = int(len(group))
        recomputed_ppl = math.exp(total_nll / total_steps)
        setting_ppl = source_ppl.get(str(setting_key), math.nan)
        record = {
            "model_profile": args.model_profile,
            "setting_key": setting_key,
            "logit_bias": float(group["logit_bias"].iloc[0]),
            "num_sequences": int(len(seq_group)),
            "num_steps": total_steps,
            "source_conditional_ppl": setting_ppl,
            "recomputed_conditional_ppl": recomputed_ppl,
            "unwatermarked_conditional_ppl": clean_ppl,
            "log_ppl_increase_vs_unwatermarked": (
                math.log(setting_ppl) - math.log(clean_ppl)
                if setting_ppl > 0 and clean_ppl > 0
                else math.nan
            ),
            "mean_compatibility_nll": float(group["compatibility_nll"].mean()),
            "mean_intervention_kl_nats": float(group["intervention_kl_nats"].mean()),
            "mean_chosen_token_nll": float(group["chosen_token_nll"].mean()),
            "adherence_rate": float(group["adheres_to_allowed_set"].mean()),
            "invalid_prefix_rate": float(group["used_fallback"].mean()),
            "recovery_step_rate": float(group["used_recovery"].mean()),
            "step_spearman_compatibility_vs_token_nll": safe_spearman(
                group["compatibility_nll"].tolist(), group["chosen_token_nll"].tolist()
            ),
            "sequence_spearman_compatibility_vs_token_nll": safe_spearman(
                seq_group["mean_compatibility_nll"].tolist(),
                seq_group["mean_chosen_token_nll"].tolist(),
            ),
        }
        for step_type, typed in group.groupby("step_type"):
            record[f"{step_type}_count"] = int(len(typed))
            record[f"{step_type}_mean_allowed_mass"] = float(typed["allowed_mass"].mean())
            record[f"{step_type}_mean_compatibility_nll"] = float(
                typed["compatibility_nll"].mean()
            )
            record[f"{step_type}_adherence_rate"] = float(
                typed["adheres_to_allowed_set"].mean()
            )
        records.append(record)
    return pd.DataFrame(records)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = json.loads(Path(args.detailed_results).read_text(encoding="utf-8"))
    selected_keys = (
        {item.strip() for item in args.setting_keys.split(",") if item.strip()}
        if args.setting_keys
        else None
    )
    settings = [
        setting
        for setting in source["settings"]
        if selected_keys is None or str(setting["setting_key"]) in selected_keys
    ]
    if not settings:
        raise RuntimeError("No matching settings found in detailed results.")

    token_to_bucket = np.load(Path(args.partition_dir) / "token_to_bucket.npy")
    codebook = EccCodebook(block_len=args.block_len, vt_a=args.vt_a)
    model = load_model(args)
    device = model_device(model)
    bucket_indices = {
        bucket: torch.as_tensor(
            np.flatnonzero(token_to_bucket == bucket), dtype=torch.long, device=device
        )
        for bucket in (0, 1, 2)
    }
    if any(len(indices) == 0 for indices in bucket_indices.values()):
        raise RuntimeError("All three partition buckets must be non-empty.")

    step_rows: List[Dict[str, Any]] = []
    sequence_rows: List[Dict[str, Any]] = []
    started = time.perf_counter()
    processed = 0

    for setting in settings:
        setting_key = str(setting["setting_key"])
        logit_bias = float(setting["logit_bias"])
        generated = setting["generated"]
        if args.max_samples is not None:
            generated = generated[: args.max_samples]

        for sequence_index, row in enumerate(generated):
            prompt_ids = [int(item) for item in row["prompt_token_ids"]]
            generated_ids = [int(item) for item in row["generated_token_ids"]]
            generated_buckets = [int(item) for item in row["generated_bucket_seq"]]
            if len(generated_ids) != len(generated_buckets):
                raise RuntimeError("Generated token ids and bucket sequence lengths disagree.")
            if not prompt_ids or not generated_ids:
                continue
            input_ids = torch.tensor(
                [prompt_ids + generated_ids], dtype=torch.long, device=device
            )
            attention_mask = torch.ones_like(input_ids)
            with torch.inference_mode():
                output = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=False,
                    return_dict=True,
                )
                start = len(prompt_ids) - 1
                logits = output.logits[0, start : start + len(generated_ids), :].float()
                log_masses = log_bucket_masses(logits, bucket_indices)
                target_ids = torch.tensor(generated_ids, dtype=torch.long, device=device)
                chosen_nll = -torch.log_softmax(logits, dim=-1).gather(
                    -1, target_ids.unsqueeze(-1)
                ).squeeze(-1)

            admissible = reconstruct_admissible_steps(
                generated_buckets,
                feasible_codewords=codebook.feasible,
                block_len=args.block_len,
                invalid_prefix_policy=args.invalid_prefix_policy,
            )
            sequence_step_rows: List[Dict[str, Any]] = []
            for index, state in enumerate(admissible):
                log_p = {bucket: float(log_masses[bucket][index].item()) for bucket in (0, 1, 2)}
                allowed = state["allowed_buckets"]
                is_legacy_invalid = bool(state["used_fallback"])
                log_payload_mass = float(np.logaddexp(log_p[0], log_p[1]))
                log_allowed = (
                    math.nan
                    if is_legacy_invalid
                    else float(np.logaddexp.reduce([log_p[bucket] for bucket in allowed]))
                )
                if is_legacy_invalid:
                    # Legacy generation removed the boundary bucket but imposed no
                    # 0/1 constraint after the prefix became invalid.
                    intervention_kl = -log_payload_mass
                elif state["step_type"] == "boundary":
                    intervention_kl = -log_allowed
                else:
                    disallowed = [bucket for bucket in (0, 1) if bucket not in allowed]
                    log_disallowed = (
                        float(np.logaddexp.reduce([log_p[bucket] for bucket in disallowed]))
                        if disallowed
                        else -math.inf
                    )
                    intervention_kl = soft_intervention_kl_nats(
                        log_allowed_mass=log_allowed,
                        log_disallowed_payload_mass=log_disallowed,
                        logit_bias=logit_bias,
                    )
                record = {
                    "model_profile": args.model_profile,
                    "setting_key": setting_key,
                    "logit_bias": logit_bias,
                    "sequence_index": int(sequence_index),
                    **state,
                    "allowed_buckets_json": json.dumps(allowed),
                    "p_bucket0": math.exp(log_p[0]),
                    "p_bucket1": math.exp(log_p[1]),
                    "p_boundary": math.exp(log_p[2]),
                    "bucket_log_odds_1_over_0": log_p[1] - log_p[0],
                    "allowed_mass": math.exp(log_allowed) if math.isfinite(log_allowed) else math.nan,
                    "compatibility_nll": -log_allowed,
                    "intervention_kl_nats": intervention_kl,
                    "chosen_token_nll": float(chosen_nll[index].item()),
                    "chosen_token_id": int(generated_ids[index]),
                }
                sequence_step_rows.append(record)
            step_rows.extend(sequence_step_rows)
            sequence_rows.append(
                {
                    "model_profile": args.model_profile,
                    "setting_key": setting_key,
                    "logit_bias": logit_bias,
                    "sequence_index": int(sequence_index),
                    "num_steps": int(len(sequence_step_rows)),
                    "mean_compatibility_nll": float(
                        np.nanmean([item["compatibility_nll"] for item in sequence_step_rows])
                    ),
                    "mean_intervention_kl_nats": float(
                        np.mean([item["intervention_kl_nats"] for item in sequence_step_rows])
                    ),
                    "mean_chosen_token_nll": float(
                        np.mean([item["chosen_token_nll"] for item in sequence_step_rows])
                    ),
                    "adherence_rate": float(
                        np.nanmean([
                            item["adheres_to_allowed_set"]
                            if item["adheres_to_allowed_set"] is not None
                            else math.nan
                            for item in sequence_step_rows
                        ])
                    ),
                }
            )
            processed += 1
            if processed % args.checkpoint_every == 0:
                save_frames(output_dir, step_rows, sequence_rows)
                elapsed = time.perf_counter() - started
                print(
                    f"[progress] {args.model_profile}: {processed} sequences in {elapsed:.1f}s "
                    f"({elapsed / processed:.3f}s/sequence)",
                    flush=True,
                )
            del output, logits, input_ids, attention_mask, chosen_nll

    save_frames(output_dir, step_rows, sequence_rows)
    step_frame = pd.DataFrame(step_rows)
    sequence_frame = pd.DataFrame(sequence_rows)
    summary = summarize(step_frame, sequence_frame, settings, args)
    summary.to_csv(output_dir / "bucket_compatibility_summary.csv", index=False)
    (output_dir / "bucket_compatibility_config.json").write_text(
        json.dumps(vars(args), indent=2), encoding="utf-8"
    )
    elapsed = time.perf_counter() - started
    print(summary.to_string(index=False))
    print(f"[done] {processed} sequences in {elapsed:.1f}s", flush=True)
    del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
