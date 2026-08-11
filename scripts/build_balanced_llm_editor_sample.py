#!/usr/bin/env python
"""Build a deterministic balanced subset from corrected LLM-editor results."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd


MOTIVATION_TO_INTENT = {
    "grammar_polish": "benign",
    "clarity_improvement": "benign",
    "style_softening": "benign",
    "claim_distortion": "malicious",
    "stance_shift": "malicious",
    "source_spoofing": "malicious",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select an outcome-independent balanced LLM-editor sample."
    )
    parser.add_argument("--delta5-details", required=True)
    parser.add_argument("--delta20-details", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--per-bias-motivation", type=int, default=12)
    parser.add_argument("--seed", type=int, default=1234)
    return parser.parse_args()


def stable_stratum_seed(seed: int, bias: int, motivation: str) -> int:
    payload = f"{int(seed)}|{int(bias)}|{motivation}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def used_mask(frame: pd.DataFrame) -> pd.Series:
    return frame["used"].astype(str).str.strip().str.lower().isin({"true", "1"})


def validate_frame(frame: pd.DataFrame, bias: int) -> pd.DataFrame:
    required = {
        "sequence_index",
        "motivation",
        "intent_label",
        "used",
        "accepted_edit_json",
        "edited_text",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"delta={bias}: missing required columns {missing}")

    selected = frame.loc[used_mask(frame)].copy()
    selected["logit_bias"] = int(bias)
    selected["sequence_index"] = selected["sequence_index"].astype(int)
    if selected.duplicated(["sequence_index", "motivation"]).any():
        raise ValueError(f"delta={bias}: duplicate sequence/motivation keys")

    unknown = sorted(set(selected["motivation"]) - set(MOTIVATION_TO_INTENT))
    if unknown:
        raise ValueError(f"delta={bias}: unknown motivations {unknown}")
    expected_intent = selected["motivation"].map(MOTIVATION_TO_INTENT)
    mismatch = selected["intent_label"].astype(str) != expected_intent
    if mismatch.any():
        bad = selected.loc[
            mismatch,
            ["sequence_index", "motivation", "intent_label"],
        ].head(10)
        raise ValueError(
            f"delta={bias}: motivation/intent mismatch:\n{bad.to_string(index=False)}"
        )
    return selected


def select_balanced(
    frames: Dict[int, pd.DataFrame],
    per_bias_motivation: int,
    seed: int,
) -> tuple[pd.DataFrame, List[Dict[str, object]]]:
    if per_bias_motivation < 1:
        raise ValueError("--per-bias-motivation must be positive")

    selected_parts: List[pd.DataFrame] = []
    strata: List[Dict[str, object]] = []
    for bias in sorted(frames):
        frame = frames[bias]
        for motivation in MOTIVATION_TO_INTENT:
            candidates = frame.loc[frame["motivation"] == motivation].copy()
            available = len(candidates)
            if available < per_bias_motivation:
                raise ValueError(
                    f"delta={bias}, motivation={motivation}: requested "
                    f"{per_bias_motivation}, only {available} accepted rows available"
                )
            stratum_seed = stable_stratum_seed(seed, bias, motivation)
            sample = candidates.sample(
                n=per_bias_motivation,
                replace=False,
                random_state=stratum_seed,
            ).copy()
            sample["selection_seed"] = int(seed)
            sample["selection_stratum"] = f"delta{bias}:{motivation}"
            selected_parts.append(sample)
            strata.append(
                {
                    "logit_bias": int(bias),
                    "motivation": motivation,
                    "intent_label": MOTIVATION_TO_INTENT[motivation],
                    "available": int(available),
                    "selected": int(per_bias_motivation),
                    "stratum_seed": int(stratum_seed),
                }
            )

    combined = pd.concat(selected_parts, ignore_index=True)
    combined = combined.sort_values(
        ["logit_bias", "motivation", "sequence_index"],
        kind="stable",
    ).reset_index(drop=True)
    combined.insert(0, "balanced_sample_id", range(len(combined)))
    return combined, strata


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


def summarize_group(
    frame: pd.DataFrame,
    *,
    logit_bias: int,
    intent_label: str,
    motivation: str,
) -> Dict[str, object]:
    tp = int(frame["TP"].sum())
    fp = int(frame["FP"].sum())
    fn = int(frame["FN"].sum())
    tn = int(frame["TN"].sum())
    event_hits = int(frame["event_loc_hit"].sum())
    event_total = int(frame["event_total_overall"].sum())

    candidate_weights = frame["num_edited_blocks"].astype(float)
    candidate_weight_total = float(candidate_weights.sum())
    mean_candidate_size = safe_ratio(
        float((frame["mean_candidate_size"].astype(float) * candidate_weights).sum()),
        candidate_weight_total,
    )
    return {
        "logit_bias": int(logit_bias),
        "intent_label": intent_label,
        "motivation": motivation,
        "num_samples": int(len(frame)),
        "mean_edited_blocks": float(frame["num_edited_blocks"].mean()),
        "mean_block_edit_rate": float(frame["block_edit_rate"].mean()),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "block_tpr": safe_ratio(tp, tp + fn),
        "block_far": safe_ratio(fp, fp + tn),
        "event_loc_hit": event_hits,
        "event_total_overall": event_total,
        "candidate_coverage": safe_ratio(event_hits, event_total),
        "mean_candidate_size": mean_candidate_size,
    }


def build_result_tables(
    combined: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = {
        "TP",
        "FP",
        "FN",
        "TN",
        "event_loc_hit",
        "event_total_overall",
        "num_edited_blocks",
        "block_edit_rate",
        "mean_candidate_size",
    }
    missing = sorted(required - set(combined.columns))
    if missing:
        raise ValueError(f"Cannot summarize balanced sample; missing columns {missing}")

    motivation_rows: List[Dict[str, object]] = []
    paper_rows: List[Dict[str, object]] = []
    for bias in sorted(int(value) for value in combined["logit_bias"].unique()):
        bias_frame = combined.loc[combined["logit_bias"] == bias]
        paper_rows.append(
            summarize_group(
                bias_frame,
                logit_bias=bias,
                intent_label="ALL",
                motivation="ALL",
            )
        )
        for intent_label in ("benign", "malicious"):
            intent_frame = bias_frame.loc[
                bias_frame["intent_label"] == intent_label
            ]
            paper_rows.append(
                summarize_group(
                    intent_frame,
                    logit_bias=bias,
                    intent_label=intent_label,
                    motivation="ALL",
                )
            )

        for motivation in MOTIVATION_TO_INTENT:
            group = bias_frame.loc[bias_frame["motivation"] == motivation]
            motivation_rows.append(
                summarize_group(
                    group,
                    logit_bias=bias,
                    intent_label=MOTIVATION_TO_INTENT[motivation],
                    motivation=motivation,
                )
            )

    ordered_columns: Sequence[str] = (
        "logit_bias",
        "intent_label",
        "motivation",
        "num_samples",
        "mean_edited_blocks",
        "mean_block_edit_rate",
        "TP",
        "FP",
        "FN",
        "TN",
        "block_tpr",
        "block_far",
        "event_loc_hit",
        "event_total_overall",
        "candidate_coverage",
        "mean_candidate_size",
    )
    paper_table = pd.DataFrame(paper_rows, columns=ordered_columns)
    motivation_table = pd.DataFrame(motivation_rows, columns=ordered_columns)
    return paper_table, motivation_table


def main() -> None:
    args = parse_args()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    source_paths = {
        5: Path(args.delta5_details).resolve(),
        20: Path(args.delta20_details).resolve(),
    }
    frames = {
        bias: validate_frame(pd.read_csv(path), bias)
        for bias, path in source_paths.items()
    }
    combined, strata = select_balanced(
        frames,
        per_bias_motivation=int(args.per_bias_motivation),
        seed=int(args.seed),
    )

    paper_table, motivation_table = build_result_tables(combined)

    combined.to_csv(output / "llm_editor_balanced_all.csv", index=False)
    for bias in sorted(frames):
        combined.loc[combined["logit_bias"] == bias].to_csv(
            output / f"llm_editor_balanced_delta{bias}.csv",
            index=False,
        )
    paper_table.to_csv(
        output / "llm_editor_balanced_result_table.csv",
        index=False,
    )
    motivation_table.to_csv(
        output / "llm_editor_balanced_summary_by_motivation.csv",
        index=False,
    )

    counts_by_bias = {
        str(int(key)): int(value)
        for key, value in combined["logit_bias"].value_counts().sort_index().items()
    }
    counts_by_intent = {
        str(key): int(value)
        for key, value in combined["intent_label"].value_counts().sort_index().items()
    }
    counts_by_motivation = {
        str(key): int(value)
        for key, value in combined["motivation"].value_counts().sort_index().items()
    }
    manifest = {
        "selection_protocol": (
            "deterministic uniform sampling within each logit_bias x motivation "
            "stratum; no detector or judge outcome is used"
        ),
        "seed": int(args.seed),
        "per_bias_motivation": int(args.per_bias_motivation),
        "num_selected": int(len(combined)),
        "source_files": {
            str(bias): str(path) for bias, path in source_paths.items()
        },
        "counts_by_bias": counts_by_bias,
        "counts_by_intent": counts_by_intent,
        "counts_by_motivation": counts_by_motivation,
        "result_tables": {
            "paper_facing": "llm_editor_balanced_result_table.csv",
            "by_motivation": "llm_editor_balanced_summary_by_motivation.csv",
        },
        "metric_definitions": {
            "block_tpr": "sum(TP) / (sum(TP) + sum(FN))",
            "block_far": "sum(FP) / (sum(FP) + sum(TN))",
            "candidate_coverage": (
                "sum(event_loc_hit) / sum(event_total_overall)"
            ),
            "mean_candidate_size": (
                "per-sample mean candidate size weighted by num_edited_blocks"
            ),
        },
        "strata": strata,
        "selected_keys": [
            {
                "logit_bias": int(row.logit_bias),
                "sequence_index": int(row.sequence_index),
                "motivation": str(row.motivation),
                "intent_label": str(row.intent_label),
            }
            for row in combined.itertuples(index=False)
        ],
    }
    (output / "balanced_selection_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "num_selected": manifest["num_selected"],
        "counts_by_bias": manifest["counts_by_bias"],
        "counts_by_intent": manifest["counts_by_intent"],
        "counts_by_motivation": manifest["counts_by_motivation"],
    }, indent=2))


if __name__ == "__main__":
    main()
