from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROFILES = ("qwen3-8b", "mistral-7b-instruct-v0.3", "opt-125m")
BIASES = (2.0, 5.0, 20.0, 50.0)
TOLERANCES = {2.0: {0, 1, 2}, 5.0: {0, 1}, 20.0: {0}, 50.0: {0}}


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def validate_ecc(root: Path, adaptive: bool) -> None:
    for profile in PROFILES:
        run = root / profile
        summary = pd.read_csv(require(run / "summary.csv"))
        detail = json.loads(require(run / "detailed_results.json").read_text())
        settings = detail["settings"]
        assert len(settings) == len(BIASES)
        assert {float(row["logit_bias"]) for row in settings} == set(BIASES)
        assert {bool(row["adaptive"]) for row in settings} == {adaptive}
        expected_rows = 12 * sum(len(TOLERANCES[bias]) for bias in BIASES)
        assert len(summary) == expected_rows, (profile, len(summary), expected_rows)
        for bias, group in summary.groupby("logit_bias"):
            assert set(group["tolerance"].astype(int)) == TOLERANCES[float(bias)]
        for column in (
            "ppl",
            "ppl_conditional_token_ids",
            "ppl_unconditional_token_ids",
            "ppl_suffix_text",
        ):
            assert np.isfinite(summary[column]).all(), (profile, column)
        for setting in settings:
            assert setting["adaptive_invalid_prefix_policy"] == "nearest_feasible"
            assert len(setting["generated"]) == 256
            for generated in setting["generated"]:
                assert generated["num_closed_blocks"] == 18
                assert generated["stop_reason"] == "target_closed_blocks"
        print(f"[ok] ECC {'adaptive' if adaptive else 'non-adaptive'}: {profile}")


def validate_clean(root: Path) -> None:
    for profile in PROFILES:
        run = root / profile
        rows = pd.read_csv(require(run / "unwatermarked_generations.csv"))
        config = json.loads(require(run / "unwatermarked_config.json").read_text())
        assert len(rows) == 256
        assert set(rows["num_generated_tokens"].astype(int)) == {144}
        for value in config["ppl_metrics"].values():
            assert np.isfinite(float(value))
        print(f"[ok] unwatermarked: {profile}")


def validate_editor(root: Path) -> None:
    for profile in PROFILES:
        for bias in BIASES:
            label = f"{bias:g}".replace(".", "p")
            run = root / profile / f"delta{label}"
            details = pd.read_csv(require(run / "llm_editor_details.csv"))
            assert len(details) == 256
            for tolerance in TOLERANCES[bias]:
                corrected = (
                    run
                    / "tolerance_sweep"
                    / f"tolerance_{tolerance}"
                    / "llm_editor_details_corrected.csv"
                )
                require(corrected)
            print(f"[ok] LLM editor: {profile}, delta={bias:g}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", default="outputs/paper_rerun_20260811", type=Path
    )
    parser.add_argument(
        "--stage",
        choices=("all", "source", "quality", "clean", "editor"),
        default="all",
    )
    args = parser.parse_args()
    if args.stage in {"all", "source"}:
        validate_ecc(args.root / "ecc_adaptive_nearest", adaptive=True)
    if args.stage in {"all", "quality"}:
        validate_ecc(args.root / "ecc_nonadaptive_quality", adaptive=False)
    if args.stage in {"all", "clean"}:
        validate_clean(args.root / "unwatermarked_controls")
    if args.stage in {"all", "editor"}:
        validate_editor(args.root / "llm_editor")
    print("PAPER RERUN VALIDATION PASSED")


if __name__ == "__main__":
    main()
