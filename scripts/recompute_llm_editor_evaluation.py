#!/usr/bin/env python
"""Recompute saved LLM-editor metrics with corrected candidate coordinates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_llm_editor_experiment import build_summary_dataframe
from watermark_project.ecc_detector import (
    EccCodebook,
    ParsedBlock,
    evaluate_predictions_with_provenance,
    parsed_block_exceeds_tolerance,
)
from watermark_project.edits import EditEvent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tolerance", type=int, default=None)
    return parser.parse_args()


def edit_event_from_dict(value: Dict[str, Any]) -> EditEvent:
    location = value["loc"]
    return EditEvent(
        etype=str(value["etype"]),
        loc=(str(location[0]), int(location[1])),
        value_before=value.get("value_before"),
        value_after=value.get("value_after"),
    )


def gt_events_from_instructions(
    instructions: List[Dict[str, Any]],
    num_blocks: int,
) -> List[List[EditEvent]]:
    events: List[List[EditEvent]] = [[] for _ in range(num_blocks)]
    for instruction in instructions:
        for block_id, block_events in instruction.get("block_events", {}).items():
            index = int(block_id)
            if 0 <= index < num_blocks:
                events[index].extend(
                    edit_event_from_dict(item) for item in block_events
                )
    return events


def parsed_block_from_dict(value: Dict[str, Any]) -> ParsedBlock:
    info = dict(value.get("info") or {})
    for key in (
        "payload_distance",
        "total_distance",
        "boundary_state",
        "observed_span_start",
        "observed_span_end_exclusive",
        "observed_boundary_index",
    ):
        if key not in info and value.get(key) is not None:
            info[key] = value[key]
    return ParsedBlock(
        block_tokens=[int(x) for x in value.get("observed_payload_tokens", [])],
        flag=bool(value.get("exceeds_tolerance", False)),
        etype="multi",
        candidates=[
            (str(item[0]), int(item[1]))
            for item in value.get("candidate_edit_locations", [])
        ],
        decoded_codeword=(
            [int(x) for x in value["decoded_codeword"]]
            if value.get("decoded_codeword") is not None
            else None
        ),
        is_boundary_edited=bool(value.get("is_boundary_edited", False)),
        boundary_edit_type=value.get("boundary_edit_type"),
        info=info,
    )


def main() -> None:
    args = parse_args()
    source = Path(args.source_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    details = pd.read_csv(source / "llm_editor_details.csv")
    instruction_records = json.loads(
        (source / "llm_edit_instructions.json").read_text(encoding="utf-8")
    )
    instructions_by_key = {
        (int(item["sequence_index"]), str(item["motivation"])): item
        for item in instruction_records
    }
    config = json.loads(
        (source / "llm_editor_config.json").read_text(encoding="utf-8")
    )["args"]
    block_len = int(config["block_len"])
    num_blocks = 18
    source_tolerance = int(config["tolerance"])
    tolerance = source_tolerance if args.tolerance is None else int(args.tolerance)
    if tolerance < 0:
        raise ValueError("--tolerance must be non-negative.")
    codebook = EccCodebook(block_len, int(config["vt_a"]))
    dummy_blocks = [codebook.feasible[0].copy() for _ in range(num_blocks)]

    corrected_rows: List[Dict[str, Any]] = []
    for _, source_row in details.iterrows():
        row = source_row.to_dict()
        if not bool(row.get("used", False)):
            corrected_rows.append(row)
            continue
        key = (int(row["sequence_index"]), str(row["motivation"]))
        record = instructions_by_key[key]
        gt_events = gt_events_from_instructions(
            record["validated_instructions"],
            num_blocks,
        )
        pred_details = json.loads(str(row["pred_blocks_detailed_json"]))
        predictions = [parsed_block_from_dict(item) for item in pred_details]
        for prediction in predictions:
            prediction.flag = bool(
                parsed_block_exceeds_tolerance(
                    prediction,
                    tolerance=tolerance,
                    codebook=codebook,
                )
            )
        provenance = json.loads(str(row["edited_token_provenance_json"]))
        evaluation = evaluate_predictions_with_provenance(
            original_payload_blocks=dummy_blocks,
            gt_events_per_block=gt_events,
            pred_blocks=predictions,
            observed_provenance=provenance,
            tolerance=tolerance,
            codebook=codebook,
        )

        for metric in (
            "TP",
            "FP",
            "FN",
            "TN",
            "block_tpr",
            "block_far",
            "candidate_coverage",
            "event_loc_hit",
            "event_total_overall",
        ):
            row[f"old_{metric}"] = row.get(metric)
        row.update(
            {
                "TP": int(evaluation["TP"]),
                "FP": int(evaluation["FP"]),
                "FN": int(evaluation["FN"]),
                "TN": int(evaluation["TN"]),
                "block_tpr": float(evaluation["block_tpr"]),
                "block_far": float(evaluation["block_far"]),
                "candidate_coverage": float(
                    evaluation["event_coverage_overall"]
                ),
                "event_loc_hit": int(evaluation["event_loc_hit"]),
                "event_total_overall": int(
                    evaluation["event_total_overall"]
                ),
                "mean_candidate_size": float(
                    evaluation["mean_candidate_size"]
                ),
                "source_candidate_locations_json": json.dumps(
                    evaluation["source_candidate_locations"]
                ),
                "parsed_to_source_blocks_json": json.dumps(
                    evaluation["parsed_to_source_blocks"]
                ),
                "candidate_coordinate_system": (
                    "feasible_reference_codeword"
                ),
            }
        )
        old_confusion = tuple(
            int(row[f"old_{metric}"]) for metric in ("TP", "FP", "FN", "TN")
        )
        new_confusion = tuple(
            int(row[metric]) for metric in ("TP", "FP", "FN", "TN")
        )
        if tolerance == source_tolerance and old_confusion != new_confusion:
            raise RuntimeError(
                f"{key}: candidate-only correction changed block confusion "
                f"{old_confusion} -> {new_confusion}"
            )
        corrected_rows.append(row)

    corrected = pd.DataFrame(corrected_rows)
    summary = build_summary_dataframe(corrected_rows)
    corrected.to_csv(output / "llm_editor_details_corrected.csv", index=False)
    summary.to_csv(output / "llm_editor_summary_corrected.csv", index=False)

    used = corrected[corrected["used"] == True].copy()  # noqa: E712
    confusion_matches_source = all(
        used[f"old_{metric}"].astype(int).equals(used[metric].astype(int))
        for metric in ("TP", "FP", "FN", "TN")
    )
    report = {
        "source_dir": str(source),
        "output_dir": str(output),
        "num_rows": len(corrected),
        "num_used": len(used),
        "source_tolerance": source_tolerance,
        "evaluated_tolerance": tolerance,
        "block_confusion_unchanged": (
            confusion_matches_source if tolerance == source_tolerance else None
        ),
        "block_confusion_matches_source": confusion_matches_source,
        "old_event_hits": int(used["old_event_loc_hit"].sum()),
        "corrected_event_hits": int(used["event_loc_hit"].sum()),
        "event_total": int(used["event_total_overall"].sum()),
        "old_candidate_coverage": float(
            used["old_event_loc_hit"].sum()
            / used["old_event_total_overall"].sum()
        ),
        "corrected_candidate_coverage": float(
            used["event_loc_hit"].sum()
            / used["event_total_overall"].sum()
        ),
        "candidate_coordinate_system": "feasible_reference_codeword",
    }
    (output / "recompute_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
