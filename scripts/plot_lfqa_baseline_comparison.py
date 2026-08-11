from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


METHODS = (
    ("ecc", "Ours (ECC)", "#1f5a4a", "o"),
    ("kgw", "KGW", "#c14924", "s"),
    ("zhao_aol_aligator", "Zhao-AOL", "#2676a3", "^"),
    ("waterseeker", "WaterSeeker", "#a17c22", "D"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot matched LFQA block TPR/FAR for ECC and KGW-based baselines."
    )
    parser.add_argument("--ecc-summary", type=Path, required=True)
    parser.add_argument("--baseline-summary", type=Path, required=True)
    parser.add_argument("--model-profile", default="qwen3-8b")
    parser.add_argument("--logit-bias", type=float, default=20.0)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def select_rows(
    frame: pd.DataFrame,
    scheme: str,
    logit_bias: float,
    model_profile: str | None = None,
) -> pd.DataFrame:
    selected = frame[
        (frame["scheme"].astype(str) == scheme)
        & ((frame["logit_bias"].astype(float) - logit_bias).abs() < 1e-9)
    ].copy()
    if model_profile is not None and "model_profile" in selected.columns:
        selected = selected[selected["model_profile"].astype(str) == model_profile]
    required = {
        "edit_rate",
        "attack_max_edits_per_block",
        "block_tpr",
        "block_far",
    }
    missing = required.difference(selected.columns)
    if missing:
        raise ValueError(f"Missing required columns for {scheme}: {sorted(missing)}")
    if selected.empty:
        raise ValueError(
            f"No rows for scheme={scheme}, bias={logit_bias}, model={model_profile}"
        )
    return selected


def main() -> None:
    args = parse_args()
    ecc = pd.read_csv(args.ecc_summary)
    baselines = pd.read_csv(args.baseline_summary)
    rows = {
        "ecc": select_rows(ecc, "ecc", args.logit_bias, args.model_profile),
        "kgw": select_rows(baselines, "kgw", args.logit_bias),
        "zhao_aol_aligator": select_rows(
            baselines, "zhao_aol_aligator", args.logit_bias
        ),
        "waterseeker": select_rows(baselines, "waterseeker", args.logit_bias),
    }

    expected_rates = [0.2, 0.4, 0.6, 0.8]
    expected_budgets = [1, 2, 3]
    for scheme, frame in rows.items():
        observed = set(
            zip(
                frame["edit_rate"].astype(float),
                frame["attack_max_edits_per_block"].astype(int),
            )
        )
        expected = {(rate, budget) for rate in expected_rates for budget in expected_budgets}
        if observed != expected:
            raise ValueError(
                f"Incomplete setting grid for {scheme}: missing={sorted(expected-observed)}, "
                f"extra={sorted(observed-expected)}"
            )

    fig, axes = plt.subplots(2, 3, figsize=(14.5, 8.2), sharex=True, sharey="row")
    for column, budget in enumerate(expected_budgets):
        for row_index, (metric, ylabel) in enumerate(
            (("block_tpr", "Block TPR"), ("block_far", "Block FAR"))
        ):
            ax = axes[row_index, column]
            for scheme, label, color, marker in METHODS:
                frame = rows[scheme]
                subset = frame[
                    frame["attack_max_edits_per_block"].astype(int) == budget
                ].sort_values("edit_rate")
                ax.plot(
                    subset["edit_rate"],
                    subset[metric],
                    label=label,
                    color=color,
                    marker=marker,
                    linewidth=2.4,
                    markersize=7.5,
                )
            ax.set_title(f"k = {budget}", fontsize=17, pad=8)
            ax.set_xticks(expected_rates)
            ax.set_ylim(-0.02, 1.02)
            ax.grid(alpha=0.25, linewidth=0.9)
            ax.tick_params(labelsize=13)
            if column == 0:
                ax.set_ylabel(ylabel, fontsize=16)
            if row_index == 1:
                ax.set_xlabel("Edit rate", fontsize=16)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        fontsize=14,
        frameon=False,
        bbox_to_anchor=(0.5, 1.01),
    )
    fig.suptitle(
        f"Matched LFQA local-edit detection ({args.model_profile}, delta={args.logit_bias:g})",
        fontsize=19,
        y=0.955,
    )
    fig.tight_layout(rect=(0.02, 0.02, 0.98, 0.90))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.output_dir / "lfqa_local_detection_comparison"
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)
    print(stem.with_suffix(".png"))
    print(stem.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
