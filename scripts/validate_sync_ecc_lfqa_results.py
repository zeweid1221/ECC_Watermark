"""Validate completeness and finite metrics for a sync-ECC LFQA run."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--expected-samples", type=int, default=256)
    args = parser.parse_args()

    root = Path(args.result_dir).resolve()
    required = [
        root / "summary.csv",
        root / "details.csv",
        root / "generated.json",
        root / "config.json",
        root / "prompts.txt",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    summary = pd.read_csv(root / "summary.csv")
    details = pd.read_csv(root / "details.csv")
    generated = json.loads((root / "generated.json").read_text(encoding="utf-8"))
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    run_args = config["args"]
    biases = [float(value) for value in run_args["logit_bias_values"]]
    rates = [float(value) for value in run_args["edit_rates"]]
    budgets = [int(value) for value in run_args["attack_max_edits_per_blocks"]]
    attacks = [str(value) for value in run_args["attack_types"]]
    expected_summary = len(biases) * len(rates) * len(budgets) * len(attacks)
    expected_details = expected_summary * int(args.expected_samples)
    expected_generated = len(biases) * int(args.expected_samples)

    if len(summary) != expected_summary:
        raise RuntimeError(f"Expected {expected_summary} summary rows, found {len(summary)}.")
    if len(details) != expected_details:
        raise RuntimeError(f"Expected {expected_details} detail rows, found {len(details)}.")
    if len(generated) != expected_generated:
        raise RuntimeError(f"Expected {expected_generated} generations, found {len(generated)}.")
    if set(summary["scheme"]) != {"sync_ecc_accepted"}:
        raise RuntimeError(f"Unexpected schemes: {sorted(set(summary['scheme']))}")

    summary_key = [
        "logit_bias",
        "attack_type",
        "edit_rate",
        "attack_max_edits_per_block",
    ]
    detail_key = summary_key + ["sequence_index"]
    if summary.duplicated(summary_key).any():
        raise RuntimeError("Duplicate summary settings detected.")
    if details.duplicated(detail_key).any():
        raise RuntimeError("Duplicate detail rows detected.")
    if set(summary["attack_type"]) != set(attacks):
        raise RuntimeError("Attack-type coverage does not match config.json.")
    if set(int(value) for value in summary["num_sequences_used"]) != {args.expected_samples}:
        raise RuntimeError("One or more settings used an incomplete sequence set.")

    metric_columns = [
        "block_tpr",
        "block_far",
        "candidate_coverage",
        "mean_candidate_set_size",
        "ppl",
        "ppl_conditional_token_ids",
        "ppl_unconditional_token_ids",
        "mean_tag_adherence",
        "mean_clean_vt_valid_rate",
    ]
    for column in metric_columns:
        if column not in summary:
            raise KeyError(column)
        if not all(math.isfinite(float(value)) for value in summary[column]):
            raise RuntimeError(f"Nonfinite values found in {column}.")
    for column in ("block_tpr", "block_far", "candidate_coverage", "mean_tag_adherence"):
        if not summary[column].between(0.0, 1.0).all():
            raise RuntimeError(f"Values outside [0, 1] found in {column}.")

    report = {
        "status": "passed",
        "result_dir": str(root),
        "summary_rows": len(summary),
        "detail_rows": len(details),
        "generated_rows": len(generated),
        "biases": biases,
        "edit_rates": rates,
        "attack_budgets": budgets,
        "attack_types": attacks,
        "samples_per_setting": int(args.expected_samples),
    }
    (root / "validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
