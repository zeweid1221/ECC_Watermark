"""Compare legacy and nearest-feasible ECC generation results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROFILES = ("qwen3-8b", "mistral-7b-instruct-v0.3", "opt-125m")
CANONICAL_TOLERANCE = {2.0: 2, 5.0: 1, 20.0: 0}
PAIR_KEYS = (
    "scheme",
    "watermark_mode",
    "adaptive",
    "logit_bias",
    "edit_rate",
    "attack_max_edits_per_block",
    "tolerance",
)
METRICS = (
    "block_tpr",
    "block_far",
    "event_coverage_overall",
    "mean_clean_valid_blocks_per_used_sequence",
)
PPL_METRICS = (
    "ppl",
    "ppl_suffix_text",
    "ppl_unconditional_token_ids",
    "ppl_conditional_token_ids",
)
REQUIRED_FINITE_METRICS = METRICS + PPL_METRICS + (
    "block_precision",
    "document_false_alarm_rate",
    "mean_false_blocks_per_document",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--nearest-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    paired_frames: list[pd.DataFrame] = []
    tolerance_frames: list[pd.DataFrame] = []
    ppl_rows: list[dict[str, object]] = []
    validation: dict[str, object] = {
        "profiles": list(PROFILES),
        "canonical_tolerance": CANONICAL_TOLERANCE,
        "profile_checks": {},
    }

    for profile in PROFILES:
        legacy_dir = args.legacy_root / profile
        nearest_dir = args.nearest_root / profile
        legacy = pd.read_csv(legacy_dir / "summary.csv")
        nearest = pd.read_csv(nearest_dir / "summary.csv")

        nearest_canonical = nearest[
            nearest.apply(
                lambda row: int(row["tolerance"])
                == CANONICAL_TOLERANCE[float(row["logit_bias"])],
                axis=1,
            )
        ]
        paired = legacy.merge(
            nearest_canonical,
            on=list(PAIR_KEYS),
            suffixes=("_legacy", "_nearest"),
            validate="one_to_one",
        )
        paired.insert(0, "model_profile", profile)
        paired_frames.append(paired)

        tolerance = nearest.copy()
        tolerance.insert(0, "model_profile", profile)
        tolerance_frames.append(tolerance)

        for bias in sorted(CANONICAL_TOLERANCE):
            old_row = legacy[legacy["logit_bias"] == bias].iloc[0]
            new_row = nearest[nearest["logit_bias"] == bias].iloc[0]
            row: dict[str, object] = {"model_profile": profile, "logit_bias": bias}
            for metric in PPL_METRICS:
                row[f"{metric}_legacy"] = old_row[metric]
                row[f"{metric}_nearest"] = new_row[metric]
                row[f"{metric}_delta"] = new_row[metric] - old_row[metric]
            ppl_rows.append(row)

        required_numeric = nearest[list(REQUIRED_FINITE_METRICS)]
        optional_numeric_nan_columns = [
            column
            for column in nearest.select_dtypes(include=[np.number]).columns
            if nearest[column].isna().any() and column not in REQUIRED_FINITE_METRICS
        ]
        prompt_hashes = {
            "legacy": sha256(legacy_dir / "prompts.txt"),
            "nearest": sha256(nearest_dir / "prompts.txt"),
        }
        validation["profile_checks"][profile] = {
            "legacy_summary_rows": len(legacy),
            "nearest_summary_rows": len(nearest),
            "paired_canonical_rows": len(paired),
            "nearest_required_metrics_finite": bool(
                np.isfinite(required_numeric.to_numpy()).all()
            ),
            "optional_numeric_nan_columns": optional_numeric_nan_columns,
            "prompt_sha256": prompt_hashes,
            "prompts_identical": prompt_hashes["legacy"] == prompt_hashes["nearest"],
            "nearest_tolerances_by_bias": {
                str(float(bias)): sorted(
                    int(value)
                    for value in nearest.loc[
                        nearest["logit_bias"] == bias, "tolerance"
                    ].unique()
                )
                for bias in sorted(nearest["logit_bias"].unique())
            },
        }

    paired_all = pd.concat(paired_frames, ignore_index=True)
    tolerance_all = pd.concat(tolerance_frames, ignore_index=True)
    ppl = pd.DataFrame(ppl_rows)

    aggregate = paired_all.groupby(
        ["model_profile", "logit_bias"], as_index=False
    ).agg(
        **{
            f"{metric}_{version}": (f"{metric}_{version}", "mean")
            for metric in METRICS
            for version in ("legacy", "nearest")
        }
    )
    for metric in METRICS:
        aggregate[f"{metric}_delta"] = (
            aggregate[f"{metric}_nearest"] - aggregate[f"{metric}_legacy"]
        )

    tolerance_summary = tolerance_all.groupby(
        ["model_profile", "logit_bias", "tolerance"], as_index=False
    )[
        [
            "block_tpr",
            "block_far",
            "event_coverage_overall",
            "block_precision",
            "document_false_alarm_rate",
            "mean_false_blocks_per_document",
        ]
    ].mean()

    paired_all.to_csv(args.output_dir / "paired_canonical_settings.csv", index=False)
    aggregate.to_csv(args.output_dir / "aggregate_by_model_bias.csv", index=False)
    tolerance_all.to_csv(args.output_dir / "nearest_all_tolerance_rows.csv", index=False)
    tolerance_summary.to_csv(
        args.output_dir / "nearest_tolerance_summary.csv", index=False
    )
    ppl.to_csv(args.output_dir / "ppl_comparison.csv", index=False)
    (args.output_dir / "validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )

    print(aggregate.to_string(index=False))
    print(f"\nSaved comparison archive: {args.output_dir}")


if __name__ == "__main__":
    main()
