from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine per-model bucket compatibility summaries with clean PPL controls."
    )
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--ppl-summary-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_root = Path(args.input_root)
    frames = [
        pd.read_csv(path)
        for path in sorted(input_root.glob("*/bucket_compatibility_summary.csv"))
    ]
    if not frames:
        raise RuntimeError(f"No compatibility summaries found under {input_root}")
    combined = pd.concat(frames, ignore_index=True)

    ppl = pd.read_csv(args.ppl_summary_csv)
    clean = ppl[ppl["setting_type"] == "unwatermarked"][
        ["model_profile", "ppl_conditional_token_ids"]
    ].rename(
        columns={"ppl_conditional_token_ids": "unwatermarked_conditional_ppl"}
    )
    if clean["model_profile"].duplicated().any():
        raise RuntimeError("Expected exactly one unwatermarked PPL row per model.")

    combined = combined.drop(columns=["unwatermarked_conditional_ppl"], errors="ignore")
    combined = combined.merge(clean, on="model_profile", how="left", validate="many_to_one")
    if combined["unwatermarked_conditional_ppl"].isna().any():
        missing = sorted(
            combined.loc[
                combined["unwatermarked_conditional_ppl"].isna(), "model_profile"
            ].unique()
        )
        raise RuntimeError(f"Missing clean PPL controls for: {missing}")

    combined["conditional_ppl_ratio_vs_unwatermarked"] = (
        combined["source_conditional_ppl"]
        / combined["unwatermarked_conditional_ppl"]
    )
    combined["log_ppl_increase_vs_unwatermarked"] = np.log(
        combined["conditional_ppl_ratio_vs_unwatermarked"]
    )
    combined["boundary_step_fraction"] = (
        combined["boundary_count"] / combined["num_steps"]
    )
    boundary_weighted_cost = (
        combined["boundary_step_fraction"]
        * combined["boundary_mean_compatibility_nll"]
    )
    combined["boundary_compatibility_cost_share"] = (
        boundary_weighted_cost / combined["mean_compatibility_nll"]
    )

    expected_rows = 9
    if len(combined) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} model/bias rows, found {len(combined)}")
    numeric = combined.select_dtypes(include=["number"]).to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise RuntimeError("Combined compatibility summary contains non-finite values.")

    combined = combined.sort_values(["model_profile", "logit_bias"]).reset_index(drop=True)
    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)
    print(f"Saved {len(combined)} rows to {output_path}")


if __name__ == "__main__":
    main()
