#!/usr/bin/env python
"""Compute matched block-level operating points from archived Qwen3 results."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from watermark_project.config import AttackConfig
from watermark_project.ecc_detector import EccCodebook
from watermark_project.experiment import evaluate_ecc_payload_blocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-profile", default="qwen3-8b")
    parser.add_argument("--biases", default="2,5,20")
    return parser.parse_args()


def parse_list(value: object, cast=float) -> List[Any]:
    return [cast(item) for item in json.loads(str(value))]


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def auc_from_scores(labels: Sequence[int], scores: Sequence[float]) -> float:
    labels_arr = np.asarray(labels, dtype=np.int8)
    scores_arr = np.asarray(scores, dtype=np.float64)
    num_positive = int(np.sum(labels_arr == 1))
    num_negative = int(np.sum(labels_arr == 0))
    if num_positive == 0 or num_negative == 0:
        return math.nan
    order = np.argsort(scores_arr, kind="mergesort")
    sorted_scores = scores_arr[order]
    sorted_labels = labels_arr[order]
    concordant = 0.0
    negatives_before = 0
    start = 0
    while start < len(sorted_scores):
        end = start + 1
        while end < len(sorted_scores) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        tied = sorted_labels[start:end]
        tied_positive = int(np.sum(tied == 1))
        tied_negative = int(np.sum(tied == 0))
        concordant += tied_positive * (negatives_before + 0.5 * tied_negative)
        negatives_before += tied_negative
        start = end
    return float(concordant / (num_positive * num_negative))


def best_tpr_at_far(
    labels: Sequence[int],
    scores: Sequence[float],
    target_far: float,
) -> Dict[str, float]:
    labels_arr = np.asarray(labels, dtype=np.int8)
    scores_arr = np.asarray(scores, dtype=np.float64)
    candidates = [float("inf"), *sorted(np.unique(scores_arr), reverse=True), float("-inf")]
    best = {"tpr": 0.0, "far": 0.0, "threshold": float("inf")}
    for threshold in candidates:
        predictions = scores_arr > threshold
        tp = int(np.sum(predictions & (labels_arr == 1)))
        fp = int(np.sum(predictions & (labels_arr == 0)))
        fn = int(np.sum((~predictions) & (labels_arr == 1)))
        tn = int(np.sum((~predictions) & (labels_arr == 0)))
        far = safe_div(fp, fp + tn)
        tpr = safe_div(tp, tp + fn)
        if far <= target_far + 1e-12 and (tpr > best["tpr"] or (tpr == best["tpr"] and far > best["far"])):
            best = {"tpr": tpr, "far": far, "threshold": float(threshold)}
    return best


def first_nonzero_operating_point(
    labels: Sequence[int],
    scores: Sequence[float],
) -> Dict[str, float]:
    labels_arr = np.asarray(labels, dtype=np.int8)
    scores_arr = np.asarray(scores, dtype=np.float64)
    candidates = [*sorted(np.unique(scores_arr), reverse=True), float("-inf")]
    points: List[Dict[str, float]] = []
    for threshold in candidates:
        predictions = scores_arr > threshold
        tp = int(np.sum(predictions & (labels_arr == 1)))
        if tp == 0:
            continue
        fp = int(np.sum(predictions & (labels_arr == 0)))
        fn = int(np.sum((~predictions) & (labels_arr == 1)))
        tn = int(np.sum((~predictions) & (labels_arr == 0)))
        points.append(
            {
                "tpr": safe_div(tp, tp + fn),
                "far": safe_div(fp, fp + tn),
                "threshold": float(threshold),
            }
        )
    return min(points, key=lambda point: (point["far"], -point["tpr"]))


def summarize_records(records: pd.DataFrame) -> pd.DataFrame:
    output: List[Dict[str, Any]] = []
    group_keys = ["method", "logit_bias"]
    for key, group in records.groupby(group_keys, sort=True):
        method, bias = key
        labels = group["label"].astype(int).tolist()
        scores = group["score"].astype(float).tolist()
        per_setting_auc = []
        for _, setting in group.groupby(["edit_rate", "attack_max_edits_per_block"], sort=True):
            per_setting_auc.append(
                auc_from_scores(setting["label"].astype(int), setting["score"].astype(float))
            )
        row: Dict[str, Any] = {
            "method": method,
            "logit_bias": float(bias),
            "num_blocks": len(group),
            "num_positive_blocks": int(group["label"].sum()),
            "num_negative_blocks": int((group["label"] == 0).sum()),
            "pooled_auc": auc_from_scores(labels, scores),
            "macro_setting_auc": float(np.nanmean(per_setting_auc)),
        }
        first = first_nonzero_operating_point(labels, scores)
        row["minimum_nonzero_far"] = first["far"]
        row["tpr_at_minimum_nonzero_far"] = first["tpr"]
        for target in (0.05, 0.10):
            point = best_tpr_at_far(labels, scores, target)
            suffix = f"{int(round(target * 100)):02d}"
            row[f"tpr_at_far_{suffix}"] = point["tpr"]
            row[f"realized_far_{suffix}"] = point["far"]
            row[f"threshold_at_far_{suffix}"] = point["threshold"]
        output.append(row)
    return pd.DataFrame(output)


def find_ecc_setting(settings: Sequence[Dict[str, Any]], bias: float) -> Dict[str, Any]:
    matches = [
        setting
        for setting in settings
        if setting["scheme"] == "ecc"
        and bool(setting["adaptive"])
        and math.isclose(float(setting["logit_bias"]), float(bias), abs_tol=1e-12)
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one ECC setting for bias {bias}, found {len(matches)}.")
    return matches[0]


def build_ecc_records(
    source_dir: Path,
    corrected_dir: Path,
    biases: Iterable[float],
) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    config = json.loads((source_dir / "run_config.json").read_text(encoding="utf-8"))
    detailed = json.loads((source_dir / "detailed_results.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(corrected_dir / "summary_corrected.csv")
    codebook = EccCodebook(
        block_len=int(config["ecc"]["block_len"]),
        vt_a=int(config["ecc"]["vt_a"]),
        boundary_symbol=int(config["ecc"].get("boundary_symbol", 2)),
    )
    target_blocks = int(config["target_blocks"])
    rows: List[Dict[str, Any]] = []
    validation: List[Dict[str, Any]] = []
    selected = summary[summary["logit_bias"].astype(float).isin([float(x) for x in biases])]
    for progress, (_, setting_row) in enumerate(selected.iterrows(), start=1):
        bias = float(setting_row["logit_bias"])
        edit_rate = float(setting_row["edit_rate"])
        attack_budget = int(setting_row["attack_max_edits_per_block"])
        tolerance = int(setting_row["tolerance"])
        setting = find_ecc_setting(detailed["settings"], bias)
        attack = AttackConfig(
            edit_rate=edit_rate,
            allow_boundary_edit=bool(config["allow_boundary_edit"]),
            boundary_edit_modes=tuple(config["boundary_edit_modes"]),
            attack_max_edits_per_block=attack_budget,
            edit_count_mode=str(config["edit_count_mode"]),
        )
        attack_seed = int(config["generation_seed"]) + int(edit_rate * 1000) + 10000 * attack_budget
        totals = {key: 0 for key in ("TP", "FP", "FN", "TN")}
        score_flag_mismatches = 0
        print(
            f"[ECC {progress}/{len(selected)}] bias={bias:g} rate={edit_rate:g} k={attack_budget}",
            flush=True,
        )
        for sequence_index, record in enumerate(setting["generated"]):
            original_blocks = [
                [int(value) for value in block]
                for block in record["generation_time_blocks"][:target_blocks]
            ]
            result = evaluate_ecc_payload_blocks(
                original_payload_blocks=original_blocks,
                codebook=codebook,
                attack=attack,
                decoder_budget=int(config["decoder_max_edits_per_block"]),
                rng=random.Random(attack_seed + sequence_index),
                tolerance=tolerance,
            )
            evaluation = result["evaluation"]
            labels = [int(value) for value in evaluation["source_gt_flags"]]
            scores = [float(value) for value in evaluation["source_anomaly_scores"]]
            flags = [int(value) for value in evaluation["source_pred_flags"]]
            threshold_flags = [int(score > tolerance) for score in scores]
            score_flag_mismatches += sum(a != b for a, b in zip(flags, threshold_flags))
            for label, flag in zip(labels, flags):
                if label and flag:
                    totals["TP"] += 1
                elif label:
                    totals["FN"] += 1
                elif flag:
                    totals["FP"] += 1
                else:
                    totals["TN"] += 1
            for block_index, (label, score) in enumerate(zip(labels, scores)):
                rows.append(
                    {
                        "method": "ECC-IW",
                        "logit_bias": bias,
                        "edit_rate": edit_rate,
                        "attack_max_edits_per_block": attack_budget,
                        "sequence_index": sequence_index,
                        "block_index": block_index,
                        "label": label,
                        "score": score,
                    }
                )
        archived = {key: int(setting_row[key]) for key in totals}
        validation.append(
            {
                "method": "ECC-IW",
                "logit_bias": bias,
                "edit_rate": edit_rate,
                "attack_max_edits_per_block": attack_budget,
                "score_flag_mismatches": score_flag_mismatches,
                "confusion_matches_archive": totals == archived,
                **{f"recomputed_{key}": value for key, value in totals.items()},
                **{f"archived_{key}": value for key, value in archived.items()},
            }
        )
    return pd.DataFrame(rows), validation


def build_cw_records(
    details_path: Path,
    biases: Iterable[float],
) -> tuple[pd.DataFrame, List[Dict[str, Any]]]:
    details = pd.read_csv(details_path)
    details = details[details["logit_bias"].astype(float).isin([float(x) for x in biases])]
    rows: List[Dict[str, Any]] = []
    validation: List[Dict[str, Any]] = []
    for _, row in details.iterrows():
        scores = parse_list(row["block_scores"], float)
        labels = parse_list(row["gt_blocks"], int)
        predictions = parse_list(row["pred_blocks"], int)
        threshold = float(row["block_threshold"])
        threshold_predictions = [int(score < threshold) for score in scores]
        method = f"CW-{row['pattern']}"
        mismatch = sum(a != b for a, b in zip(predictions, threshold_predictions))
        validation.append(
            {
                "method": method,
                "logit_bias": float(row["logit_bias"]),
                "edit_rate": float(row["edit_rate"]),
                "attack_max_edits_per_block": int(row["attack_max_edits_per_block"]),
                "sequence_index": int(row["sequence_index"]),
                "score_flag_mismatches": mismatch,
            }
        )
        for block_index, (label, score) in enumerate(zip(labels, scores)):
            rows.append(
                {
                    "method": method,
                    "logit_bias": float(row["logit_bias"]),
                    "edit_rate": float(row["edit_rate"]),
                    "attack_max_edits_per_block": int(row["attack_max_edits_per_block"]),
                    "sequence_index": int(row["sequence_index"]),
                    "block_index": block_index,
                    "label": int(label),
                    "score": -float(score),
                }
            )
    return pd.DataFrame(rows), validation


def main() -> None:
    args = parse_args()
    archive = Path(args.archive_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    biases = [float(item) for item in args.biases.split(",") if item.strip()]

    ecc_source = archive / "ecc" / "source_runs" / "soft_delta2_5_20" / args.model_profile
    ecc_corrected = archive / "ecc" / "corrected_evaluation" / "local_edit_detection" / args.model_profile
    cw_details = (
        archive
        / "supporting"
        / "comparison_baselines"
        / "combinatorial_watermark_original_threshold"
        / args.model_profile
        / "details.csv"
    )
    ecc_records, ecc_validation = build_ecc_records(ecc_source, ecc_corrected, biases)
    cw_records, cw_validation = build_cw_records(cw_details, biases)
    records = pd.concat([ecc_records, cw_records], ignore_index=True)
    summary = summarize_records(records)

    validation = {
        "ecc_settings": len(ecc_validation),
        "ecc_all_confusion_matches_archive": all(
            row["confusion_matches_archive"] for row in ecc_validation
        ),
        "ecc_total_score_flag_mismatches": int(
            sum(row["score_flag_mismatches"] for row in ecc_validation)
        ),
        "cw_rows": len(cw_validation),
        "cw_total_score_flag_mismatches": int(
            sum(row["score_flag_mismatches"] for row in cw_validation)
        ),
        "scope": "Qwen3 LFQA block-level local detection; ECC and closest CW patterns",
        "fixed_far_note": (
            "TPR@FAR values describe the empirical ROC envelope on the pooled attacked blocks; "
            "they are not deployment thresholds selected on an independent calibration split."
        ),
    }
    if not validation["ecc_all_confusion_matches_archive"]:
        raise RuntimeError("Recomputed ECC confusion counts do not match the corrected archive.")
    if validation["ecc_total_score_flag_mismatches"] != 0:
        raise RuntimeError("ECC continuous scores do not reproduce tolerance decisions.")
    if validation["cw_total_score_flag_mismatches"] != 0:
        raise RuntimeError("CW continuous scores do not reproduce original-threshold decisions.")

    records.to_parquet(output / "block_scores.parquet", index=False)
    summary.to_csv(output / "matched_operating_points.csv", index=False)
    pd.DataFrame(ecc_validation).to_csv(output / "ecc_validation.csv", index=False)
    (output / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
