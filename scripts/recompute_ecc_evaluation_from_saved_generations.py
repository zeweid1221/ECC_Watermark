#!/usr/bin/env python
"""Recompute ECC attack metrics from saved generation-time blocks."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from watermark_project.config import AttackConfig
from watermark_project.ecc_detector import EccCodebook
from watermark_project.edits import (
    apply_edits_to_payload_blocks,
)
from watermark_project.experiment import evaluate_ecc_payload_blocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--setting-index", type=int, default=None)
    parser.add_argument("--max-settings", type=int, default=None)
    parser.add_argument("--max-sequences", type=int, default=None)
    return parser.parse_args()


def setting_for_row(
    settings: Sequence[Dict[str, Any]],
    row: pd.Series,
) -> Dict[str, Any]:
    candidates = [
        setting
        for setting in settings
        if str(setting["scheme"]) == str(row["scheme"])
        and str(setting["watermark_mode"]) == str(row["watermark_mode"])
        and bool(setting["adaptive"]) == bool(row["adaptive"])
        and math.isclose(
            float(setting["logit_bias"]),
            float(row["logit_bias"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one generation setting, found {len(candidates)}.")
    return candidates[0]


def safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def recompute_setting(
    source_row: pd.Series,
    generated: Sequence[Dict[str, Any]],
    config: Dict[str, Any],
    codebook: EccCodebook,
    max_sequences: int | None,
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    attack_budget = int(source_row["attack_max_edits_per_block"])
    edit_rate = float(source_row["edit_rate"])
    tolerance = int(source_row["tolerance"])
    attack = AttackConfig(
        edit_rate=edit_rate,
        allow_boundary_edit=bool(config["allow_boundary_edit"]),
        boundary_edit_modes=tuple(config["boundary_edit_modes"]),
        attack_max_edits_per_block=attack_budget,
        edit_count_mode=str(config["edit_count_mode"]),
    )
    attack_seed = (
        int(config["generation_seed"])
        + int(edit_rate * 1000)
        + 10000 * attack_budget
    )
    target_blocks = int(config["target_blocks"])
    boundary_symbol = int(config["ecc"].get("boundary_symbol", 2))

    totals = {
        key: 0
        for key in (
            "TP",
            "FP",
            "FN",
            "TN",
            "codeword_recovery_hit",
            "codeword_recovery_total",
            "block_loc_hit",
            "loc_total_overall",
            "event_loc_hit",
            "event_total_overall",
            "event_total_sub",
            "event_total_insert",
            "event_total_delete",
        )
    }
    event_hits = {"sub": 0.0, "insert": 0.0, "delete": 0.0}
    candidate_weighted_sum = 0.0
    candidate_weighted_n = 0
    net_zero_removed = 0
    old_positive_blocks = 0
    detail_rows: List[Dict[str, Any]] = []

    selected = list(generated)
    if max_sequences is not None:
        selected = selected[: int(max_sequences)]
    for sequence_index, record in enumerate(selected):
        original_blocks = [
            [int(x) for x in block]
            for block in record["generation_time_blocks"][:target_blocks]
        ]
        if len(original_blocks) != target_blocks:
            raise RuntimeError(
                f"sequence {sequence_index}: expected {target_blocks} saved blocks, "
                f"found {len(original_blocks)}"
            )

        old_observed, old_events, old_sequence = apply_edits_to_payload_blocks(
            payload_blocks=original_blocks,
            edit_rate=edit_rate,
            allow_boundary_edit=bool(config["allow_boundary_edit"]),
            boundary_edit_modes=tuple(config["boundary_edit_modes"]),
            max_edits_per_block=attack_budget,
            edit_count_mode=str(config["edit_count_mode"]),
            boundary_symbol=boundary_symbol,
            rng=random.Random(attack_seed + sequence_index),
        )
        core_result = evaluate_ecc_payload_blocks(
            original_payload_blocks=original_blocks,
            codebook=codebook,
            attack=attack,
            decoder_budget=int(config["decoder_max_edits_per_block"]),
            rng=random.Random(attack_seed + sequence_index),
            tolerance=tolerance,
        )
        observed_blocks = core_result["observed_blocks"]
        net_events = core_result["gt_events_per_block"]
        observed_sequence = core_result["observed_sequence"]
        if old_observed != observed_blocks or old_sequence != observed_sequence:
            raise RuntimeError("Corrected provenance changed the attacked sequence.")

        old_positive = sum(bool(events) for events in old_events)
        net_positive = sum(bool(events) for events in net_events)
        removed = sum(
            bool(old) and not bool(net)
            for old, net in zip(old_events, net_events)
        )
        old_positive_blocks += old_positive
        net_zero_removed += removed

        evaluation = core_result["evaluation"]
        for key in totals:
            if key in evaluation:
                totals[key] += int(evaluation[key])
        for edit_type in event_hits:
            event_hits[edit_type] += (
                float(evaluation[f"event_coverage_{edit_type}"])
                * int(evaluation[f"event_total_{edit_type}"])
            )
        candidate_weighted_sum += (
            float(evaluation["mean_candidate_size"])
            * int(evaluation["loc_total_overall"])
        )
        candidate_weighted_n += int(evaluation["loc_total_overall"])

        detail_rows.append(
            {
                "sequence_index": int(sequence_index),
                "used": True,
                "num_valid_blocks": target_blocks,
                "num_gt_blocks": target_blocks,
                "num_pred_blocks": int(evaluation["num_pred_blocks"]),
                "old_positive_blocks": int(old_positive),
                "net_positive_blocks": int(net_positive),
                "net_zero_gt_blocks_removed": int(removed),
                "TP": int(evaluation["TP"]),
                "FP": int(evaluation["FP"]),
                "FN": int(evaluation["FN"]),
                "TN": int(evaluation["TN"]),
                "block_tpr": float(evaluation["block_tpr"]),
                "block_far": float(evaluation["block_far"]),
                "event_loc_hit": int(evaluation["event_loc_hit"]),
                "event_total_overall": int(evaluation["event_total_overall"]),
                "event_coverage_overall": float(
                    evaluation["event_coverage_overall"]
                ),
                "mean_candidate_size": float(evaluation["mean_candidate_size"]),
                "source_pred_flags": json.dumps(evaluation["source_pred_flags"]),
                "source_candidate_locations": json.dumps(
                    evaluation["source_candidate_locations"]
                ),
                "parsed_to_source_blocks": json.dumps(
                    evaluation["parsed_to_source_blocks"]
                ),
            }
        )

    summary = source_row.to_dict()
    summary.update(
        {
            "num_sequences_total": len(selected),
            "num_sequences_used": len(selected),
            "num_sequences_skipped": 0,
            "TP": totals["TP"],
            "FP": totals["FP"],
            "FN": totals["FN"],
            "TN": totals["TN"],
            "block_tpr": safe_div(totals["TP"], totals["TP"] + totals["FN"]),
            "block_far": safe_div(totals["FP"], totals["FP"] + totals["TN"]),
            "codeword_recovery_acc": safe_div(
                totals["codeword_recovery_hit"],
                totals["codeword_recovery_total"],
            ),
            "localization_acc_overall": safe_div(
                totals["block_loc_hit"],
                totals["loc_total_overall"],
            ),
            "loc_total_overall": totals["loc_total_overall"],
            "event_coverage_overall": safe_div(
                totals["event_loc_hit"],
                totals["event_total_overall"],
            ),
            "event_coverage_sub": safe_div(
                event_hits["sub"],
                totals["event_total_sub"],
            ),
            "event_coverage_insert": safe_div(
                event_hits["insert"],
                totals["event_total_insert"],
            ),
            "event_coverage_delete": safe_div(
                event_hits["delete"],
                totals["event_total_delete"],
            ),
            "event_total_overall": totals["event_total_overall"],
            "event_total_sub": totals["event_total_sub"],
            "event_total_insert": totals["event_total_insert"],
            "event_total_delete": totals["event_total_delete"],
            "mean_candidate_size": safe_div(
                candidate_weighted_sum,
                candidate_weighted_n,
            ),
            "old_positive_blocks": int(old_positive_blocks),
            "net_zero_gt_blocks_removed": int(net_zero_removed),
            "gt_semantics": "final_net_structural_edits",
            "candidate_coordinate_system": "feasible_reference_codeword",
        }
    )
    setting_columns = {
        key: source_row[key]
        for key in (
            "scheme",
            "watermark_mode",
            "adaptive",
            "logit_bias",
            "edit_rate",
            "attack_max_edits_per_block",
            "tolerance",
        )
    }
    return summary, [{**setting_columns, **row} for row in detail_rows]


def main() -> None:
    args = parse_args()
    source = Path(args.source_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    config = json.loads((source / "run_config.json").read_text(encoding="utf-8"))
    detailed = json.loads(
        (source / "detailed_results.json").read_text(encoding="utf-8")
    )
    source_summary = pd.read_csv(source / "summary.csv")
    if args.setting_index is not None:
        source_summary = source_summary.iloc[
            [int(args.setting_index)]
        ].copy()
    if args.max_settings is not None:
        source_summary = source_summary.head(int(args.max_settings)).copy()

    codebook = EccCodebook(
        block_len=int(config["ecc"]["block_len"]),
        vt_a=int(config["ecc"]["vt_a"]),
        boundary_symbol=int(config["ecc"].get("boundary_symbol", 2)),
    )
    summary_rows: List[Dict[str, Any]] = []
    detail_rows: List[Dict[str, Any]] = []
    for progress_index, (_, row) in enumerate(
        source_summary.iterrows(),
        start=1,
    ):
        setting = setting_for_row(detailed["settings"], row)
        print(
            f"[{progress_index}/{len(source_summary)}] "
            f"bias={row['logit_bias']:g} k={int(row['attack_max_edits_per_block'])} "
            f"rate={row['edit_rate']:g}",
            flush=True,
        )
        summary, details = recompute_setting(
            row,
            setting["generated"],
            config,
            codebook,
            args.max_sequences,
        )
        summary_rows.append(summary)
        detail_rows.extend(details)

    corrected_summary = pd.DataFrame(summary_rows)
    corrected_details = pd.DataFrame(detail_rows)
    corrected_summary.to_csv(output / "summary_corrected.csv", index=False)
    corrected_details.to_csv(output / "ecc_details_corrected.csv", index=False)

    metric_columns = [
        "TP",
        "FP",
        "FN",
        "TN",
        "block_tpr",
        "block_far",
        "event_coverage_overall",
        "mean_candidate_size",
    ]
    key_columns = [
        "scheme",
        "watermark_mode",
        "adaptive",
        "logit_bias",
        "edit_rate",
        "attack_max_edits_per_block",
        "tolerance",
    ]
    old = source_summary[key_columns + metric_columns].copy()
    old = old.rename(columns={column: f"old_{column}" for column in metric_columns})
    new = corrected_summary[
        key_columns
        + metric_columns
        + ["old_positive_blocks", "net_zero_gt_blocks_removed"]
    ].copy()
    new = new.rename(
        columns={column: f"corrected_{column}" for column in metric_columns}
    )
    comparison = old.merge(
        new,
        on=key_columns,
        how="inner",
        validate="one_to_one",
    )
    for metric in ("block_tpr", "block_far", "event_coverage_overall", "mean_candidate_size"):
        comparison[f"delta_{metric}"] = (
            comparison[f"corrected_{metric}"] - comparison[f"old_{metric}"]
        )
    comparison.to_csv(output / "old_vs_corrected.csv", index=False)

    report = {
        "source_dir": str(source),
        "output_dir": str(output),
        "num_summary_rows": len(corrected_summary),
        "num_detail_rows": len(corrected_details),
        "net_zero_gt_blocks_removed": int(
            corrected_summary["net_zero_gt_blocks_removed"].sum()
        ),
        "attacked_sequences_unchanged": True,
        "gt_semantics": "final_net_structural_edits",
        "candidate_coordinate_system": "feasible_reference_codeword",
    }
    (output / "recompute_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
