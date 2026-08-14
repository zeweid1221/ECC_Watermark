from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROFILES = ("qwen3-8b", "mistral-7b-instruct-v0.3", "opt-125m")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the boundary-eighth ECC sweep.")
    parser.add_argument(
        "--partition-root",
        default="outputs/partitions",
    )
    parser.add_argument(
        "--result-root",
        default="outputs/ecc_boundary_eighth_20260813/adaptive_nearest",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    partition_root = Path(args.partition_root)
    result_root = Path(args.result_root)
    for profile in PROFILES:
        partition_dir = partition_root / f"{profile}-boundary-eighth-semantic-v2"
        summary = json.loads((partition_dir / "bucket_summary.json").read_text())
        eligible = int(summary["eligible_vocab_size"])
        expected_boundary = round(eligible / 8)
        assert int(summary["num_bucket2"]) == expected_boundary
        assert abs(int(summary["num_bucket0"]) - int(summary["num_bucket1"])) <= 1
        assert summary["boundary_allocation_strategy"] == "eligible_vocab_fraction"

        run_dir = result_root / profile
        frame = pd.read_csv(run_dir / "summary.csv")
        config = json.loads((run_dir / "run_config.json").read_text())
        assert len(frame) == 72
        assert set(frame["logit_bias"].astype(float)) == {2.0, 5.0, 20.0}
        assert set(frame["adaptive"].astype(str).str.lower()) == {"true"}
        assert set(frame["edit_rate"].astype(float)) == {0.2, 0.4, 0.6, 0.8}
        assert set(frame["attack_max_edits_per_block"].astype(int)) == {1, 2, 3}
        assert set(frame["num_sequences_used"].astype(int)) == {256}
        assert set(frame["mean_valid_blocks_per_used_sequence"].astype(float)) == {18.0}
        assert np.isfinite(frame["ppl_conditional_token_ids"].astype(float)).all()
        assert config["ecc_adaptive_modes"] == [True]
        assert config["generation_protocol"]["adaptive_invalid_prefix_policy"] == "nearest_feasible"
        print(
            f"{profile}: boundary={expected_boundary}, rows={len(frame)}, "
            f"PPL={sorted(frame['ppl_conditional_token_ids'].unique().tolist())}"
        )
    print("ALL BOUNDARY-EIGHTH ECC RESULTS PASSED")


if __name__ == "__main__":
    main()
