from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


EDIT_RATES = [0.2, 0.4, 0.6, 0.8]

TPR = {
    ("Ours", 1): [1.0000, 0.9973, 0.9957, 0.9932],
    ("Ours", 2): [0.9703, 0.9705, 0.9668, 0.9627],
    ("Ours", 3): [0.9650, 0.9620, 0.9713, 0.9687],
    ("KGW", 1): [0.6922, 0.7052, 0.7246, 0.7244],
    ("KGW", 2): [0.7874, 0.8012, 0.7987, 0.8021],
    ("KGW", 3): [0.8317, 0.8234, 0.8425, 0.8447],
}

FAR = {
    ("Ours", 1): [0.0011, 0.0007, 0.0022, 0.0022],
    ("Ours", 2): [0.0018, 0.0036, 0.0042, 0.0042],
    ("Ours", 3): [0.0008, 0.0074, 0.0079, 0.0094],
    ("KGW", 1): [0.0350, 0.0571, 0.0854, 0.1383],
    ("KGW", 2): [0.0450, 0.0780, 0.1177, 0.1730],
    ("KGW", 3): [0.0474, 0.1037, 0.1498, 0.2067],
}

COLORS = {
    ("Ours", 1): "tab:blue",
    ("Ours", 2): "tab:orange",
    ("Ours", 3): "tab:green",
    ("KGW", 1): "tab:red",
    ("KGW", 2): "tab:purple",
    ("KGW", 3): "tab:brown",
}


def style_axes(ax: plt.Axes, title: str, ylabel: str, ylim: tuple[float, float]) -> None:
    ax.set_title(title, fontsize=28, pad=16)
    ax.set_xlabel("Edit rate", fontsize=24, labelpad=10)
    ax.set_ylabel(ylabel, fontsize=24, labelpad=10)
    ax.set_xticks(EDIT_RATES)
    ax.set_ylim(*ylim)
    ax.grid(True, alpha=0.30, linewidth=1.2)
    ax.tick_params(axis="both", labelsize=21, width=1.2, length=7)
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)


def plot_metric(
    metric: dict[tuple[str, int], list[float]],
    title: str,
    ylabel: str,
    ylim: tuple[float, float],
    output_path: Path,
    legend_mode: str,
) -> None:
    fig, ax = plt.subplots(figsize=(12.5, 8.0), dpi=200)

    handles = []
    labels = []
    for method in ("Ours", "KGW"):
        for k in (1, 2, 3):
            key = (method, k)
            line = ax.plot(
                EDIT_RATES,
                metric[key],
                color=COLORS[key],
                linestyle="-" if method == "Ours" else "--",
                marker="o" if method == "Ours" else "s",
                linewidth=3.2,
                markersize=10.5,
                markeredgewidth=1.4,
                label=f"{method}, k={k}",
            )[0]
            handles.append(line)
            labels.append(f"{method}, k={k}")

    style_axes(ax, title=title, ylabel=ylabel, ylim=ylim)

    if legend_mode == "top":
        legend = ax.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 1.12),
            ncol=3,
            fontsize=20,
            frameon=True,
            fancybox=True,
            framealpha=0.95,
        )
    else:
        legend = ax.legend(
            handles,
            labels,
            loc="upper left",
            fontsize=20,
            frameon=True,
            fancybox=True,
            framealpha=0.95,
        )
    legend.get_frame().set_linewidth(1.2)

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94) if legend_mode == "top" else None)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    output_dir = Path(__file__).resolve().parents[1] / "outputs" / "final_updated_figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_metric(
        metric=TPR,
        title="Block-level TPR under different edit budgets",
        ylabel="Block-level TPR",
        ylim=(0.65, 1.02),
        output_path=output_dir / "block_tpr_updated_fixed18.png",
        legend_mode="top",
    )
    plot_metric(
        metric=TPR,
        title="Block-level TPR under different edit budgets",
        ylabel="Block-level TPR",
        ylim=(0.65, 1.02),
        output_path=output_dir / "tpr_vs_edit_rate_by_k.png",
        legend_mode="top",
    )
    plot_metric(
        metric=FAR,
        title="Block-level FAR under different edit budgets",
        ylabel="Block-level FAR",
        ylim=(0.0, 0.21),
        output_path=output_dir / "block_far_updated_fixed18.png",
        legend_mode="inside",
    )
    plot_metric(
        metric=FAR,
        title="Block-level FAR under different edit budgets",
        ylabel="Block-level FAR",
        ylim=(0.0, 0.21),
        output_path=output_dir / "far_vs_edit_rate_by_k.png",
        legend_mode="inside",
    )

    print(output_dir / "block_tpr_updated_fixed18.png")
    print(output_dir / "block_far_updated_fixed18.png")
    print(output_dir / "tpr_vs_edit_rate_by_k.png")
    print(output_dir / "far_vs_edit_rate_by_k.png")


if __name__ == "__main__":
    main()
