#!/usr/bin/env python
"""Recompute block metrics using the prior method's token-level threshold."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

from build_paper_results_archive_v2 import (
    PROFILES,
    aggregate_comparison,
    build_paired_comparison,
    load_ecc_rows,
    write_checksums,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", required=True)
    return parser.parse_args()


def safe_div(numerator: int, denominator: int) -> float:
    return float(numerator / denominator) if denominator else 0.0


def canonical_strict_threshold(
    clean_scores: Sequence[float],
    target_far: float,
) -> Tuple[float, float]:
    """Largest observed score threshold with Pr[score < tau] <= target_far."""
    scores = np.asarray(clean_scores, dtype=np.float64)
    if scores.size == 0:
        raise ValueError("Cannot calibrate from an empty clean score set.")
    candidates = np.unique(scores)
    valid = [
        float(candidate)
        for candidate in candidates
        if float(np.mean(scores < candidate)) <= float(target_far) + 1e-12
    ]
    if not valid:
        raise RuntimeError("The minimum observed score must always be a valid threshold.")
    threshold = max(valid)
    clean_alarm_rate = float(np.mean(scores < threshold))
    return threshold, clean_alarm_rate


def parse_float_list(value: object) -> List[float]:
    parsed = json.loads(str(value))
    return [float(item) for item in parsed]


def parse_int_list(value: object) -> List[int]:
    parsed = json.loads(str(value))
    return [int(item) for item in parsed]


def setting_thresholds(
    generated_records: Sequence[Dict[str, object]],
    target_far: float,
) -> Dict[str, Tuple[float, float]]:
    scores: Dict[str, List[float]] = {}
    for record in generated_records:
        key = str(record["setting_key"])
        scores.setdefault(key, []).extend(
            float(value) for value in record["clean_local_scores"]
        )
    return {
        key: canonical_strict_threshold(values, target_far)
        for key, values in scores.items()
    }


def recompute_detail_rows(
    details: pd.DataFrame,
    thresholds: Dict[str, Tuple[float, float]],
) -> pd.DataFrame:
    output = details.copy()
    output["legacy_block_threshold"] = output["block_threshold"]
    output["legacy_pred_blocks"] = output["pred_blocks"]
    for metric in ("TP", "FP", "FN", "TN", "block_tpr", "block_far"):
        output[f"legacy_{metric}"] = output[metric]

    new_thresholds: List[float] = []
    clean_alarm_rates: List[float] = []
    new_predictions: List[str] = []
    counts: Dict[str, List[float]] = {
        "TP": [],
        "FP": [],
        "FN": [],
        "TN": [],
        "block_tpr": [],
        "block_far": [],
    }

    for _, row in output.iterrows():
        setting_key = str(row["setting_key"])
        threshold, clean_alarm_rate = thresholds[setting_key]
        scores = parse_float_list(row["block_scores"])
        labels = parse_int_list(row["gt_blocks"])
        if len(scores) != len(labels):
            raise RuntimeError(f"{setting_key}: block score/label length mismatch.")

        # Algorithm 3 flags token positions whose statistic is strictly below tau_e.
        # A block alarm is the union of those original token alarms within the block.
        predictions = [int(score < threshold) for score in scores]
        tp = sum(pred == 1 and label == 1 for pred, label in zip(predictions, labels))
        fp = sum(pred == 1 and label == 0 for pred, label in zip(predictions, labels))
        fn = sum(pred == 0 and label == 1 for pred, label in zip(predictions, labels))
        tn = sum(pred == 0 and label == 0 for pred, label in zip(predictions, labels))

        new_thresholds.append(threshold)
        clean_alarm_rates.append(clean_alarm_rate)
        new_predictions.append(json.dumps(predictions))
        counts["TP"].append(tp)
        counts["FP"].append(fp)
        counts["FN"].append(fn)
        counts["TN"].append(tn)
        counts["block_tpr"].append(safe_div(tp, tp + fn))
        counts["block_far"].append(safe_div(fp, fp + tn))

    output["block_threshold"] = new_thresholds
    output["canonical_original_token_threshold"] = new_thresholds
    output["clean_token_alarm_rate_original_threshold"] = clean_alarm_rates
    output["pred_blocks"] = new_predictions
    output["block_decision_rule"] = "any_original_token_alarm_in_block"
    output["threshold_source"] = "prior_token_threshold_clean_type_i_0.1"
    for metric, values in counts.items():
        output[metric] = values
    return output


def recompute_summary(
    legacy_summary: pd.DataFrame,
    details: pd.DataFrame,
) -> pd.DataFrame:
    output = legacy_summary.copy()
    output["legacy_block_threshold"] = output["block_threshold"]
    for metric in ("TP", "FP", "FN", "TN", "block_tpr", "block_far"):
        output[f"legacy_{metric}"] = output[metric]

    group_keys = [
        "setting_key",
        "edit_rate",
        "attack_max_edits_per_block",
    ]
    grouped = {
        tuple(key if isinstance(key, tuple) else (key,)): group
        for key, group in details.groupby(group_keys, sort=False)
    }
    values: Dict[str, List[object]] = {
        "block_threshold": [],
        "canonical_original_token_threshold": [],
        "clean_token_alarm_rate_original_threshold": [],
        "TP": [],
        "FP": [],
        "FN": [],
        "TN": [],
        "block_tpr": [],
        "block_far": [],
    }
    for _, row in output.iterrows():
        key = (
            row["setting_key"],
            row["edit_rate"],
            row["attack_max_edits_per_block"],
        )
        group = grouped[key]
        tp = int(group["TP"].sum())
        fp = int(group["FP"].sum())
        fn = int(group["FN"].sum())
        tn = int(group["TN"].sum())
        threshold = float(group["canonical_original_token_threshold"].iloc[0])
        clean_alarm_rate = float(
            group["clean_token_alarm_rate_original_threshold"].iloc[0]
        )
        values["block_threshold"].append(threshold)
        values["canonical_original_token_threshold"].append(threshold)
        values["clean_token_alarm_rate_original_threshold"].append(clean_alarm_rate)
        values["TP"].append(tp)
        values["FP"].append(fp)
        values["FN"].append(fn)
        values["TN"].append(tn)
        values["block_tpr"].append(safe_div(tp, tp + fn))
        values["block_far"].append(safe_div(fp, fp + tn))
    for column, column_values in values.items():
        output[column] = column_values
    output["block_decision_rule"] = "any_original_token_alarm_in_block"
    output["threshold_source"] = "prior_token_threshold_clean_type_i_0.1"
    return output


def main() -> None:
    args = parse_args()
    archive = Path(args.archive_dir).resolve()
    source_root = archive / "comparison_baselines" / "combinatorial_watermark"
    output_root = (
        archive
        / "comparison_baselines"
        / "combinatorial_watermark_original_threshold"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    summary_frames: List[pd.DataFrame] = []
    validation_rows: List[Dict[str, object]] = []
    for profile in PROFILES:
        source = source_root / profile
        generated = json.loads((source / "generated.json").read_text(encoding="utf-8"))
        legacy_details = pd.read_csv(source / "details.csv")
        legacy_summary = pd.read_csv(source / "summary.csv")
        target_far = float(legacy_summary["target_clean_far"].iloc[0])
        thresholds = setting_thresholds(generated, target_far)
        details = recompute_detail_rows(legacy_details, thresholds)
        summary = recompute_summary(legacy_summary, details)
        summary["model_profile"] = profile
        summary_frames.append(summary)

        destination = output_root / profile
        destination.mkdir(parents=True, exist_ok=True)
        details.to_csv(destination / "details.csv", index=False)
        summary.drop(columns="model_profile").to_csv(
            destination / "summary.csv", index=False
        )
        shutil.copy2(source / "config.json", destination / "source_config.json")
        for setting_key, (threshold, clean_far) in sorted(thresholds.items()):
            validation_rows.append(
                {
                    "model_profile": profile,
                    "setting_key": setting_key,
                    "canonical_original_token_threshold": threshold,
                    "clean_token_alarm_rate": clean_far,
                    "target_clean_far": target_far,
                }
            )

    validation = pd.DataFrame(validation_rows)
    if not (validation["clean_token_alarm_rate"] <= 0.1 + 1e-12).all():
        raise RuntimeError("Original token threshold exceeds the target clean Type-I rate.")
    validation.to_csv(output_root / "threshold_validation.csv", index=False)

    original_summary = pd.concat(summary_frames, ignore_index=True)
    ecc = load_ecc_rows(archive)
    paired = build_paired_comparison(ecc, original_summary)
    paired["combinatorial_threshold_source"] = (
        "prior_token_threshold_clean_type_i_0.1"
    )
    paired["combinatorial_block_decision_rule"] = (
        "any_original_token_alarm_in_block"
    )
    aggregate = aggregate_comparison(paired)
    comparisons = archive / "comparisons"
    paired.to_csv(
        comparisons
        / "ecc_vs_combinatorial_original_threshold_all_settings.csv",
        index=False,
    )
    aggregate.to_csv(
        comparisons / "ecc_vs_combinatorial_original_threshold_aggregate.csv",
        index=False,
    )
    qwen_paired = paired[paired["model_profile"] == "qwen3-8b"].copy()
    qwen_aggregate = aggregate[
        aggregate["model_profile"] == "qwen3-8b"
    ].copy()
    qwen_paired.to_csv(
        comparisons
        / "ecc_vs_combinatorial_original_threshold_qwen3_all_settings.csv",
        index=False,
    )
    qwen_aggregate.to_csv(
        comparisons
        / "ecc_vs_combinatorial_original_threshold_qwen3_aggregate.csv",
        index=False,
    )
    qwen_paired[qwen_paired["logit_bias"].isin([20.0, 50.0])].to_csv(
        comparisons
        / "ecc_vs_combinatorial_original_threshold_qwen3_strong_bias_settings.csv",
        index=False,
    )

    methodology = """# Combinatorial Baseline Re-evaluation

The primary comparison uses the prior method's token-level edit statistic and
threshold rule. For every model, pattern, and logit bias, tau_e is calibrated
on clean watermarked token statistics so that the empirical Type-I alarm rate
Pr[score < tau_e] is at most 0.1. Attacked token positions are flagged exactly
when their local statistic is below tau_e.

For the common block-level evaluation only, a block is marked suspicious when
at least one token in that block is flagged by the original detector. This is
equivalent to comparing the minimum token statistic in that block against the
same tau_e. No separate block threshold is calibrated, and attack labels are
not used in threshold selection.

The earlier separately calibrated block-threshold artifacts are retained under
`comparison_baselines/combinatorial_watermark/` for audit purposes, but they are
not the primary prior-work comparison.
"""
    (output_root / "METHODOLOGY.md").write_text(methodology, encoding="utf-8")
    shutil.copy2(
        Path(__file__).resolve(),
        archive / "code_snapshot" / "scripts" / Path(__file__).name,
    )
    write_checksums(archive)
    print(f"Recomputed original-threshold results under {output_root}")
    print(f"Paired rows: {len(paired)}")
    print(f"Aggregate rows: {len(aggregate)}")
    print(f"Qwen3 primary rows: {len(qwen_paired)}")
    print(f"Threshold validation rows: {len(validation)}")


if __name__ == "__main__":
    main()
