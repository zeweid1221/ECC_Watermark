from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


MODEL_LABELS = {
    "qwen3-8b": "Qwen3-8B",
    "mistral-7b-instruct-v0.3": "Mistral-7B",
    "opt-125m": "OPT-125M",
}
COLORS = {
    "qwen3-8b": "#bb4d2d",
    "mistral-7b-instruct-v0.3": "#126f70",
    "opt-125m": "#7a6c3b",
}
MARKERS = {"qwen3-8b": "o", "mistral-7b-instruct-v0.3": "s", "opt-125m": "^"}
CANONICAL_TOLERANCE = {2.0: 2, 5.0: 1, 20.0: 0, 50.0: 0}


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1"})


def build_pareto_table(ecc_csv: str, quality_csv: str) -> pd.DataFrame:
    ecc = pd.read_csv(ecc_csv)
    ecc = ecc[(ecc["scheme"] == "ecc") & as_bool(ecc["adaptive"])].copy()
    if "tolerance" in ecc.columns:
        expected = ecc["logit_bias"].map(CANONICAL_TOLERANCE)
        ecc = ecc[expected.notna() & ecc["tolerance"].eq(expected)].copy()
    detection = (
        ecc.groupby(["model_profile", "logit_bias"], as_index=False)
        .agg(block_tpr=("block_tpr", "mean"), block_far=("block_far", "mean"))
    )

    quality = pd.read_csv(quality_csv)
    clean = (
        quality[quality["setting_type"] == "unwatermarked"]
        .set_index("model_profile")["ppl_conditional_token_ids"]
        .to_dict()
    )
    watermarked = quality[
        (quality["setting_type"] == "watermarked") & as_bool(quality["adaptive"])
    ].copy()
    watermarked["unwatermarked_conditional_ppl"] = watermarked["model_profile"].map(clean)
    watermarked["conditional_ppl_ratio"] = (
        watermarked["ppl_conditional_token_ids"]
        / watermarked["unwatermarked_conditional_ppl"]
    )
    columns = [
        "model_profile",
        "logit_bias",
        "unwatermarked_conditional_ppl",
        "ppl_conditional_token_ids",
        "conditional_ppl_ratio",
    ]
    return detection.merge(watermarked[columns], on=["model_profile", "logit_bias"], how="inner")


def plot(table: pd.DataFrame, output_prefix: Path) -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.15))
    for model_profile, group in table.groupby("model_profile"):
        group = group.sort_values("logit_bias")
        kwargs = {
            "color": COLORS[model_profile],
            "marker": MARKERS[model_profile],
            "linewidth": 2.0,
            "markersize": 6.5,
            "label": MODEL_LABELS[model_profile],
        }
        axes[0].plot(group["conditional_ppl_ratio"], group["block_tpr"], **kwargs)
        axes[1].plot(group["conditional_ppl_ratio"], group["block_far"], **kwargs)

    axes[0].set_title("Detection sensitivity")
    axes[0].set_ylabel("Block TPR")
    axes[1].set_title("False alarms")
    axes[1].set_ylabel("Block FAR")
    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("Conditional PPL / unwatermarked PPL")
        axis.grid(alpha=0.22, linewidth=0.7)
    axes[0].set_ylim(0.15, 1.03)
    axes[1].set_ylim(-0.02, 0.46)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output_prefix.with_suffix(".png"), dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecc-summary-csv", required=True)
    parser.add_argument("--quality-summary-csv", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--output-data-csv")
    args = parser.parse_args()
    table = build_pareto_table(args.ecc_summary_csv, args.quality_summary_csv)
    if args.output_data_csv:
        output_data = Path(args.output_data_csv)
        output_data.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output_data, index=False)
    plot(table, Path(args.output_prefix))


if __name__ == "__main__":
    main()
