from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watermark_project.reporting_metrics import (  # noqa: E402
    coerce_bool,
    document_alarm_metrics,
    editor_structural_visibility_metrics,
    safe_ratio,
)


def parse_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value


def save_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    path.with_suffix(".json").write_text(
        json.dumps(frame.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def summarize_editor_group(group: pd.DataFrame) -> Dict[str, Any]:
    visible = int(group["num_structurally_visible_edited_blocks"].sum())
    invisible = int(group["num_structurally_invisible_edited_blocks"].sum())
    visible_flagged = int(group["num_visible_edited_blocks_flagged"].sum())
    invisible_flagged = int(group["num_invisible_edited_blocks_flagged"].sum())
    tp = int(group["TP"].sum())
    fp = int(group["FP"].sum())
    fn = int(group["FN"].sum())
    tn = int(group["TN"].sum())
    return {
        "num_examples": int(len(group)),
        "num_substitute_instructions": int(group["num_substitute_instructions"].sum()),
        "num_single_token_same_bucket_substitutions": int(
            group["num_single_token_same_bucket_substitutions"].sum()
        ),
        "num_single_token_cross_bucket_substitutions": int(
            group["num_single_token_cross_bucket_substitutions"].sum()
        ),
        "num_multi_token_substitutions": int(group["num_multi_token_substitutions"].sum()),
        "num_structurally_visible_edited_blocks": visible,
        "num_structurally_invisible_edited_blocks": invisible,
        "structural_visibility_rate": safe_ratio(visible, visible + invisible),
        "num_visible_edited_blocks_flagged": visible_flagged,
        "visible_block_tpr": safe_ratio(visible_flagged, visible),
        "num_invisible_edited_blocks_flagged": invisible_flagged,
        "invisible_block_alarm_rate": safe_ratio(invisible_flagged, invisible),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": safe_ratio(tp, tp + fn),
        "block_far": safe_ratio(fp, fp + tn),
        **document_alarm_metrics(group.to_dict(orient="records")),
    }


def run_editor(args: argparse.Namespace) -> None:
    details = pd.read_csv(args.details_csv)
    token_to_bucket = np.load(Path(args.partition_dir) / "token_to_bucket.npy")
    derived_rows: List[Dict[str, Any]] = []
    for _, row in details.iterrows():
        if not coerce_bool(row.get("used", True)):
            derived_rows.append({})
            continue
        metrics = editor_structural_visibility_metrics(
            original_token_ids=parse_json(row["original_token_ids_json"]),
            original_token_block_map=parse_json(row["original_token_block_map_json"]),
            edited_structural_symbols=parse_json(row["edited_token_structural_symbols_json"]),
            edited_token_provenance=parse_json(row["edited_token_provenance_json"]),
            gt_block_flags=parse_json(row["gt_blocks"]),
            pred_block_flags=parse_json(row["pred_blocks"]),
            token_to_bucket=token_to_bucket,
            accepted_edit_json=parse_json(row["accepted_edit_json"]),
        )
        metrics["structurally_visible_gt_blocks_json"] = json.dumps(
            metrics["structurally_visible_gt_blocks_json"]
        )
        metrics["structurally_invisible_gt_blocks_json"] = json.dumps(
            metrics["structurally_invisible_gt_blocks_json"]
        )
        metrics.update(document_alarm_metrics([row.to_dict()]))
        metrics["has_false_alarm"] = bool(int(row.get("FP", 0)) > 0)
        derived_rows.append(metrics)

    derived = pd.DataFrame(derived_rows)
    base = details.drop(columns=[column for column in derived.columns if column in details.columns])
    enriched = pd.concat([base.reset_index(drop=True), derived], axis=1)
    output_dir = Path(args.output_dir)
    save_table(enriched, output_dir / "llm_editor_details_with_reporting_metrics.csv")

    for keys, name in [
        (["logit_bias"], "llm_editor_structural_visibility_by_bias.csv"),
        (["logit_bias", "intent_label"], "llm_editor_structural_visibility_by_bias_intent.csv"),
        (["logit_bias", "motivation"], "llm_editor_structural_visibility_by_bias_motivation.csv"),
    ]:
        records = []
        for values, group in enriched.groupby(keys, dropna=False):
            values = values if isinstance(values, tuple) else (values,)
            used_group = group[group["used"].map(coerce_bool)] if "used" in group else group
            records.append(
                {
                    **dict(zip(keys, values)),
                    "num_examples_total": int(len(group)),
                    "num_examples_skipped": int(len(group) - len(used_group)),
                    **summarize_editor_group(used_group),
                }
            )
        save_table(pd.DataFrame(records), output_dir / name)


def parse_labeled_paths(values: Sequence[str]) -> List[Tuple[str, Path]]:
    parsed = []
    for value in values:
        if "=" not in value:
            raise ValueError("ECC detail inputs must use LABEL=PATH syntax.")
        label, path = value.split("=", 1)
        parsed.append((label, Path(path)))
    return parsed


def summarize_ecc_group(group: pd.DataFrame) -> Dict[str, Any]:
    tp = int(group["TP"].sum())
    fp = int(group["FP"].sum())
    fn = int(group["FN"].sum())
    tn = int(group["TN"].sum())
    return {
        "num_evaluated_documents": int(len(group)),
        "mean_edited_blocks_per_document": float((group["TP"] + group["FN"]).mean()),
        "mean_clean_blocks_per_document": float((group["FP"] + group["TN"]).mean()),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": safe_ratio(tp, tp + fn),
        "block_far": safe_ratio(fp, fp + tn),
        **document_alarm_metrics(group.to_dict(orient="records")),
    }


def run_ecc(args: argparse.Namespace) -> None:
    frames = []
    for model_label, path in parse_labeled_paths(args.details_csv):
        frame = pd.read_csv(path)
        frame = frame[frame["used"].astype(str).str.lower().isin({"true", "1"})].copy()
        frame.insert(0, "model_profile", model_label)
        frame["has_false_alarm"] = frame["FP"].astype(int) > 0
        frame["block_precision"] = [
            safe_ratio(int(tp), int(tp) + int(fp)) for tp, fp in zip(frame["TP"], frame["FP"])
        ]
        frames.append(frame)
    details = pd.concat(frames, ignore_index=True)
    output_dir = Path(args.output_dir)

    exact_keys = [
        "model_profile",
        "logit_bias",
        "edit_rate",
        "attack_max_edits_per_block",
        "tolerance",
    ]
    exact_records = []
    for values, group in details.groupby(exact_keys, dropna=False):
        exact_records.append({**dict(zip(exact_keys, values)), **summarize_ecc_group(group)})
    save_table(pd.DataFrame(exact_records), output_dir / "ecc_document_alarm_by_setting.csv")

    macro_records = []
    for values, group in details.groupby(["model_profile", "logit_bias"], dropna=False):
        macro_records.append(
            {
                "model_profile": values[0],
                "logit_bias": values[1],
                **summarize_ecc_group(group),
            }
        )
    save_table(pd.DataFrame(macro_records), output_dir / "ecc_document_alarm_by_model_bias.csv")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recompute reporting metrics from saved experiment details.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    editor = subparsers.add_parser("editor")
    editor.add_argument("--details-csv", required=True)
    editor.add_argument("--partition-dir", required=True)
    editor.add_argument("--output-dir", required=True)
    editor.set_defaults(func=run_editor)

    ecc = subparsers.add_parser("ecc")
    ecc.add_argument("--details-csv", action="append", required=True, help="LABEL=PATH; repeat per model.")
    ecc.add_argument("--output-dir", required=True)
    ecc.set_defaults(func=run_ecc)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
