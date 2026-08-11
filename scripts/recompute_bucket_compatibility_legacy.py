from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analyze_bucket_compatibility import safe_spearman


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute compatibility metrics for legacy adaptive generations without "
            "counting unconstrained invalid-prefix steps as successful adherence."
        )
    )
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--previous-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def correct_steps(frame: pd.DataFrame) -> pd.DataFrame:
    corrected = frame.copy()
    invalid = corrected["used_fallback"].astype(bool)
    payload_mass = corrected["p_bucket0"].astype(float) + corrected["p_bucket1"].astype(float)
    corrected.loc[invalid, "step_type"] = "payload_invalid_prefix"
    corrected.loc[invalid, "allowed_mass"] = np.nan
    corrected.loc[invalid, "compatibility_nll"] = np.nan
    corrected.loc[invalid, "adheres_to_allowed_set"] = np.nan
    corrected.loc[invalid, "intervention_kl_nats"] = -np.log(
        payload_mass.loc[invalid].clip(lower=np.finfo(float).tiny)
    )
    corrected["prefix_status"] = np.where(
        invalid,
        "legacy_unconstrained",
        np.where(corrected["step_type"].eq("boundary"), "complete", "exact"),
    )
    corrected["used_recovery"] = False
    return corrected


def sequence_summary(steps: pd.DataFrame) -> pd.DataFrame:
    keys = ["model_profile", "setting_key", "logit_bias", "sequence_index"]
    return (
        steps.groupby(keys, as_index=False)
        .agg(
            num_steps=("step_index", "size"),
            mean_compatibility_nll=("compatibility_nll", "mean"),
            mean_intervention_kl_nats=("intervention_kl_nats", "mean"),
            mean_chosen_token_nll=("chosen_token_nll", "mean"),
            adherence_rate=("adheres_to_allowed_set", "mean"),
            invalid_prefix_rate=("used_fallback", "mean"),
        )
    )


def corrected_summary(
    steps: pd.DataFrame,
    sequences: pd.DataFrame,
    previous: pd.DataFrame,
) -> pd.DataFrame:
    records: List[Dict[str, object]] = []
    for (model, setting_key), group in steps.groupby(
        ["model_profile", "setting_key"], sort=False
    ):
        old = previous[
            previous["model_profile"].eq(model)
            & previous["setting_key"].eq(setting_key)
        ]
        if len(old) != 1:
            raise RuntimeError(f"Expected one previous summary row for {model}/{setting_key}.")
        record: Dict[str, object] = old.iloc[0].to_dict()
        seq = sequences[
            sequences["model_profile"].eq(model)
            & sequences["setting_key"].eq(setting_key)
        ]
        record.update(
            {
                "mean_compatibility_nll": float(group["compatibility_nll"].mean()),
                "mean_intervention_kl_nats": float(group["intervention_kl_nats"].mean()),
                "adherence_rate": float(group["adheres_to_allowed_set"].mean()),
                "invalid_prefix_step_rate": float(group["used_fallback"].mean()),
                "sequences_with_invalid_prefix_rate": float(
                    seq.groupby("sequence_index")["invalid_prefix_rate"].max().gt(0).mean()
                ),
                "step_spearman_compatibility_vs_token_nll": safe_spearman(
                    group["compatibility_nll"].tolist(),
                    group["chosen_token_nll"].tolist(),
                ),
                "sequence_spearman_compatibility_vs_token_nll": safe_spearman(
                    seq["mean_compatibility_nll"].tolist(),
                    seq["mean_chosen_token_nll"].tolist(),
                ),
            }
        )
        compatibility_total = float(group["compatibility_nll"].sum())
        boundary_total = float(
            group.loc[group["step_type"].eq("boundary"), "compatibility_nll"].sum()
        )
        record["boundary_compatibility_cost_share"] = (
            boundary_total / compatibility_total if compatibility_total > 0 else math.nan
        )
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
    input_root = Path(args.input_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(input_root.glob("*/bucket_compatibility_steps.parquet"))
    if not paths:
        raise FileNotFoundError(f"No step parquet files found below {input_root}.")
    raw = pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)
    corrected = correct_steps(raw)
    sequences = sequence_summary(corrected)
    previous = pd.read_csv(args.previous_summary)
    summary = corrected_summary(corrected, sequences, previous)

    corrected.to_parquet(output_dir / "bucket_compatibility_steps_corrected.parquet", index=False)
    sequences.to_csv(output_dir / "bucket_compatibility_sequences_corrected.csv", index=False)
    summary.to_csv(output_dir / "bucket_compatibility_summary_corrected.csv", index=False)
    report = {
        "source_protocol": "legacy_unconstrained",
        "correction": (
            "Invalid-prefix payload steps are excluded from bit compatibility and adherence; "
            "their boundary-masking intervention KL is retained."
        ),
        "num_steps": int(len(corrected)),
        "num_invalid_prefix_steps": int(corrected["used_fallback"].sum()),
        "invalid_prefix_step_rate": float(corrected["used_fallback"].mean()),
    }
    (output_dir / "recompute_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(summary[
        [
            "model_profile",
            "logit_bias",
            "adherence_rate",
            "payload_singleton_adherence_rate",
            "invalid_prefix_step_rate",
            "sequences_with_invalid_prefix_rate",
            "mean_intervention_kl_nats",
        ]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
