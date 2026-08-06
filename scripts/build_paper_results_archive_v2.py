#!/usr/bin/env python
"""Build the consolidated v2 paper-results archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


PROFILES = ("qwen3-8b", "mistral-7b-instruct-v0.3", "opt-125m")
EDITOR_DIRS = {
    5: "llm_editor_qwen3_delta5_source256_fixed18_aggressive_min6_max10",
    20: "llm_editor_qwen3_delta20_source256_fixed18_aggressive_min6_max10",
}
JOIN_KEYS = ("model_profile", "logit_bias", "edit_rate", "attack_max_edits_per_block")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-bundle", required=True)
    parser.add_argument("--download-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--resume-existing", action="store_true")
    return parser.parse_args()


def require_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def copy_tree(source: Path, destination: Path) -> None:
    require_path(source)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def bool_series(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def load_ecc_rows(base_bundle: Path) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for profile in PROFILES:
        soft_path = base_bundle / "local_edit_detection" / profile / "summary.csv"
        delta50_path = (
            base_bundle
            / "local_edit_detection_delta50_adaptive_ablation"
            / profile
            / "summary.csv"
        )
        soft = pd.read_csv(require_path(soft_path))
        delta50 = pd.read_csv(require_path(delta50_path))
        if "adaptive" in delta50.columns:
            delta50 = delta50[bool_series(delta50["adaptive"])].copy()
        combined = pd.concat([soft, delta50], ignore_index=True)
        combined["model_profile"] = profile
        frames.append(combined)
    result = pd.concat(frames, ignore_index=True)
    expected_biases = {2.0, 5.0, 20.0, 50.0}
    if set(result["logit_bias"].astype(float)) != expected_biases:
        raise RuntimeError("ECC rows do not cover the expected bias values.")
    expected_rows = len(PROFILES) * len(expected_biases) * 4 * 3
    if len(result) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} ECC rows; found {len(result)}.")
    return result


def load_combinatorial_rows(download_root: Path) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    root = download_root / "outputs" / "three_model_combinatorial_baseline"
    for profile in PROFILES:
        frame = pd.read_csv(require_path(root / profile / "summary.csv"))
        frame["model_profile"] = profile
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    expected_rows = len(PROFILES) * 2 * 4 * 4 * 3
    if len(result) != expected_rows:
        raise RuntimeError(
            f"Expected {expected_rows} combinatorial rows; found {len(result)}."
        )
    return result


def build_paired_comparison(ecc: pd.DataFrame, comb: pd.DataFrame) -> pd.DataFrame:
    ecc_columns = [
        *JOIN_KEYS,
        "tolerance",
        "TP",
        "FP",
        "FN",
        "TN",
        "block_tpr",
        "block_far",
        "event_coverage_overall",
        "mean_candidate_size",
        "ppl_unconditional_token_ids",
        "ppl_conditional_token_ids",
    ]
    comb_columns = [
        *JOIN_KEYS,
        "pattern",
        "num_buckets",
        "target_clean_far",
        "token_threshold",
        "block_threshold",
        "mean_pattern_adherence",
        "mean_clean_global_score",
        "TP",
        "FP",
        "FN",
        "TN",
        "block_tpr",
        "block_far",
        "token_precision",
        "token_recall",
        "token_f1",
        "token_far",
        "ppl_unconditional_token_ids",
        "ppl_conditional_token_ids",
    ]
    ecc_view = ecc[ecc_columns].rename(
        columns={
            column: f"ecc_{column}"
            for column in ecc_columns
            if column not in JOIN_KEYS
        }
    )
    comb_view = comb[comb_columns].rename(
        columns={
            column: f"combinatorial_{column}"
            for column in comb_columns
            if column not in (*JOIN_KEYS, "pattern", "num_buckets")
        }
    )
    paired = comb_view.merge(
        ecc_view,
        on=list(JOIN_KEYS),
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    if set(paired["_merge"]) != {"both"}:
        raise RuntimeError("Some combinatorial settings lack a matched ECC row.")
    paired = paired.drop(columns="_merge")
    paired["ecc_minus_combinatorial_tpr"] = (
        paired["ecc_block_tpr"] - paired["combinatorial_block_tpr"]
    )
    paired["ecc_minus_combinatorial_far"] = (
        paired["ecc_block_far"] - paired["combinatorial_block_far"]
    )
    paired["ecc_pareto_dominates"] = (
        (paired["ecc_block_tpr"] >= paired["combinatorial_block_tpr"])
        & (paired["ecc_block_far"] <= paired["combinatorial_block_far"])
        & (
            (paired["ecc_block_tpr"] > paired["combinatorial_block_tpr"])
            | (paired["ecc_block_far"] < paired["combinatorial_block_far"])
        )
    )
    paired["combinatorial_all_negative"] = (
        (paired["combinatorial_TP"] == 0)
        & (paired["combinatorial_FP"] == 0)
    )
    return paired.sort_values(
        [
            "model_profile",
            "pattern",
            "logit_bias",
            "attack_max_edits_per_block",
            "edit_rate",
        ]
    ).reset_index(drop=True)


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.astype(float).div(denominator.replace(0, np.nan).astype(float))


def aggregate_comparison(paired: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["model_profile", "pattern", "num_buckets", "logit_bias"]
    rows: List[Dict[str, object]] = []
    for keys, group in paired.groupby(group_columns, sort=True):
        row: Dict[str, object] = dict(zip(group_columns, keys))
        row.update(
            {
                "num_attack_settings": len(group),
                "ecc_macro_block_tpr": group["ecc_block_tpr"].mean(),
                "ecc_macro_block_far": group["ecc_block_far"].mean(),
                "combinatorial_macro_block_tpr": group[
                    "combinatorial_block_tpr"
                ].mean(),
                "combinatorial_macro_block_far": group[
                    "combinatorial_block_far"
                ].mean(),
                "ecc_mean_event_coverage": group[
                    "ecc_event_coverage_overall"
                ].mean(),
                "combinatorial_mean_token_precision": group[
                    "combinatorial_token_precision"
                ].mean(),
                "combinatorial_mean_token_recall": group[
                    "combinatorial_token_recall"
                ].mean(),
                "mean_pattern_adherence": group[
                    "combinatorial_mean_pattern_adherence"
                ].mean(),
                "ecc_pareto_dominance_count": int(
                    group["ecc_pareto_dominates"].sum()
                ),
                "combinatorial_all_negative_count": int(
                    group["combinatorial_all_negative"].sum()
                ),
            }
        )
        for prefix in ("ecc", "combinatorial"):
            tp = int(group[f"{prefix}_TP"].sum())
            fp = int(group[f"{prefix}_FP"].sum())
            fn = int(group[f"{prefix}_FN"].sum())
            tn = int(group[f"{prefix}_TN"].sum())
            row[f"{prefix}_pooled_TP"] = tp
            row[f"{prefix}_pooled_FP"] = fp
            row[f"{prefix}_pooled_FN"] = fn
            row[f"{prefix}_pooled_TN"] = tn
            row[f"{prefix}_pooled_block_tpr"] = tp / (tp + fn) if tp + fn else np.nan
            row[f"{prefix}_pooled_block_far"] = fp / (fp + tn) if fp + tn else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def build_editor_summary(download_root: Path) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for bias, directory in EDITOR_DIRS.items():
        details_path = download_root / "outputs" / directory / "llm_editor_details.csv"
        details = pd.read_csv(require_path(details_path))
        if len(details) != 256:
            raise RuntimeError(f"delta={bias}: expected 256 editor rows; found {len(details)}.")
        used = bool_series(details["used"])
        for (intent, motivation), group in details.groupby(
            ["intent_label", "motivation"], dropna=False
        ):
            group_used = bool_series(group["used"])
            accepted = group[group_used]
            tp = int(accepted["TP"].sum()) if len(accepted) else 0
            fp = int(accepted["FP"].sum()) if len(accepted) else 0
            fn = int(accepted["FN"].sum()) if len(accepted) else 0
            tn = int(accepted["TN"].sum()) if len(accepted) else 0
            skip_counts = (
                group.loc[~group_used, "skip_reason"]
                .fillna("unknown")
                .value_counts()
                .to_dict()
            )
            rows.append(
                {
                    "logit_bias": bias,
                    "intent_label": intent,
                    "motivation": motivation,
                    "num_total": len(group),
                    "num_used": int(group_used.sum()),
                    "num_skipped": int((~group_used).sum()),
                    "acceptance_rate": float(group_used.mean()),
                    "mean_edited_blocks": accepted["num_edited_blocks"].mean(),
                    "mean_block_edit_rate": accepted["block_edit_rate"].mean(),
                    "pooled_block_tpr": tp / (tp + fn) if tp + fn else np.nan,
                    "pooled_block_far": fp / (fp + tn) if fp + tn else np.nan,
                    "mean_candidate_coverage": accepted[
                        "candidate_coverage"
                    ].mean(),
                    "skip_reason_counts_json": json.dumps(skip_counts, sort_keys=True),
                }
            )
        rows.append(
            {
                "logit_bias": bias,
                "intent_label": "ALL",
                "motivation": "ALL",
                "num_total": len(details),
                "num_used": int(used.sum()),
                "num_skipped": int((~used).sum()),
                "acceptance_rate": float(used.mean()),
                "mean_edited_blocks": details.loc[used, "num_edited_blocks"].mean(),
                "mean_block_edit_rate": details.loc[used, "block_edit_rate"].mean(),
                "pooled_block_tpr": (
                    details.loc[used, "TP"].sum()
                    / (
                        details.loc[used, "TP"].sum()
                        + details.loc[used, "FN"].sum()
                    )
                ),
                "pooled_block_far": (
                    details.loc[used, "FP"].sum()
                    / (
                        details.loc[used, "FP"].sum()
                        + details.loc[used, "TN"].sum()
                    )
                ),
                "mean_candidate_coverage": details.loc[
                    used, "candidate_coverage"
                ].mean(),
                "skip_reason_counts_json": json.dumps(
                    details.loc[~used, "skip_reason"]
                    .fillna("unknown")
                    .value_counts()
                    .to_dict(),
                    sort_keys=True,
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["logit_bias", "intent_label", "motivation"]
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksums(root: Path) -> None:
    checksum_path = root / "checksums_sha256_v2.csv"
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path != checksum_path
    )
    rows = [
        {
            "relative_path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    pd.DataFrame(rows).to_csv(checksum_path, index=False)


def copy_new_artifacts(download_root: Path, output_dir: Path) -> None:
    outputs = require_path(download_root / "outputs")
    copy_tree(
        outputs / "three_model_combinatorial_baseline",
        output_dir / "comparison_baselines" / "combinatorial_watermark",
    )
    for bias, directory in EDITOR_DIRS.items():
        copy_tree(
            outputs / directory,
            output_dir / "llm_editor" / f"delta{bias}",
        )
    copy_tree(
        outputs / "editor_seeds",
        output_dir / "llm_editor" / "editor_seeds",
    )
    if (download_root / "logs").exists():
        copy_tree(
            download_root / "logs",
            output_dir / "execution_logs" / "combinatorial_and_editor_20260806",
        )
    for relative_path in (
        "baselines/combinatorial_watermark.py",
        "scripts/run_combinatorial_baseline.py",
        "scripts/run_llm_editor_experiment.py",
        "scripts/export_editor_seed_from_detailed_results.py",
        "msi/run_three_model_combinatorial_baseline.slurm",
        "msi/run_editor_fixed_partition.slurm",
    ):
        source = require_path(download_root / relative_path)
        destination = output_dir / "code_snapshot" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def write_v2_index(output_dir: Path, paired: pd.DataFrame, editor: pd.DataFrame) -> None:
    aggregate = pd.read_csv(
        output_dir / "comparisons" / "ecc_vs_combinatorial_aggregate.csv"
    )
    strong = aggregate[aggregate["logit_bias"].isin([20.0, 50.0])]
    index = f"""# Paper Results Archive V2

Created from the verified v1 ECC/global-verification bundle and the MSI
combinatorial/editor archive downloaded on 2026-08-06.

## Contents

- `local_edit_detection/`: three-model adaptive ECC, delta 2/5/20.
- `local_edit_detection_delta50_adaptive_ablation/`: delta 50 adaptive/non-adaptive.
- `global_verification/`: three-source and human-negative verification.
- `unwatermarked_controls/`: matched unwatermarked generations.
- `comparison_baselines/combinatorial_watermark/`: AB and ACADBCBD baseline outputs.
- `llm_editor/`: Qwen3 delta 5/20 editor outputs and exact-token seeds.
- `comparisons/`: paired and aggregated ECC-vs-combinatorial results.
- `code_snapshot/`: code used for the archived experiments.
- `execution_logs/`: retained Slurm logs.

## Validation

- Paired ECC-vs-combinatorial rows: {len(paired)}
- Expected paired rows: 288
- Strong-bias aggregate groups: {len(strong)}
- Editor total rows: {int(editor[editor["intent_label"] == "ALL"]["num_total"].sum())}
- All artifacts are indexed in `checksums_sha256_v2.csv`.

The per-setting comparison is the authoritative source for reviewer-facing claims;
aggregate tables should not replace inspection by edit rate and attack budget.
"""
    (output_dir / "PAPER_RESULT_INDEX_V2.md").write_text(index, encoding="utf-8")


def main() -> None:
    args = parse_args()
    base_bundle = require_path(Path(args.base_bundle).resolve())
    download_root = require_path(Path(args.download_root).resolve())
    output_dir = Path(args.output_dir).resolve()
    if output_dir.exists() and not args.resume_existing:
        raise FileExistsError(
            f"Refusing to overwrite existing archive directory: {output_dir}"
        )

    shutil.copytree(
        base_bundle,
        output_dir,
        dirs_exist_ok=bool(args.resume_existing),
    )
    copy_new_artifacts(download_root, output_dir)

    ecc = load_ecc_rows(base_bundle)
    combinatorial = load_combinatorial_rows(download_root)
    paired = build_paired_comparison(ecc, combinatorial)
    aggregate = aggregate_comparison(paired)
    editor = build_editor_summary(download_root)

    comparisons = output_dir / "comparisons"
    comparisons.mkdir(parents=True, exist_ok=True)
    paired.to_csv(
        comparisons / "ecc_vs_combinatorial_all_settings.csv", index=False
    )
    aggregate.to_csv(
        comparisons / "ecc_vs_combinatorial_aggregate.csv", index=False
    )
    editor.to_csv(
        comparisons / "llm_editor_acceptance_and_metrics.csv", index=False
    )
    write_v2_index(output_dir, paired, editor)
    shutil.copy2(
        Path(__file__).resolve(),
        output_dir / "code_snapshot" / "scripts" / Path(__file__).name,
    )
    write_checksums(output_dir)
    print(f"Created consolidated archive: {output_dir}")
    print(f"Paired comparison rows: {len(paired)}")
    print(f"Aggregate comparison rows: {len(aggregate)}")
    print(f"Editor summary rows: {len(editor)}")


if __name__ == "__main__":
    main()
