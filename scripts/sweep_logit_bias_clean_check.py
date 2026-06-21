from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from statistics import mean, median
from typing import Iterable, List, Sequence

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watermark_project.config import ECCConfig, GenerationSetting, ModelConfig  # noqa: E402
from watermark_project.ecc_generator import EccGenerator  # noqa: E402
from watermark_project.modeling import build_language_model, clean_text  # noqa: E402
from watermark_project.partitioning import build_vocabulary_partition  # noqa: E402


LOGIT_BIASES = [2, 3, 5, 8, 10, 15, 20, 30, 50]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ECC clean-generation logit-bias calibration sweep.",
    )
    parser.add_argument("--prompt-file", default="prompts.txt")
    parser.add_argument("--output-dir", default="outputs/logit_bias_clean_check")
    parser.add_argument("--backend", choices=["mock", "hf"], default="mock")
    parser.add_argument("--model-name", default="mock-lm")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--target-blocks", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--non-adaptive", action="store_true")
    return parser.parse_args()


def load_prompts(prompt_file: str, prompt_count: int = 10) -> List[str]:
    path = Path(prompt_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    prompts = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            cleaned = clean_text(line)
            if cleaned:
                prompts.append(cleaned)
            if len(prompts) >= prompt_count:
                break
    if len(prompts) < prompt_count:
        raise RuntimeError(f"Need exactly {prompt_count} cleaned prompts, but found only {len(prompts)} in {path}.")
    return prompts


def edit_distance(a: Sequence[int], b: Sequence[int]) -> int:
    prev = list(range(len(b) + 1))
    for i, av in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, bv in enumerate(b, start=1):
            cur[j] = min(
                prev[j] + 1,
                cur[j - 1] + 1,
                prev[j - 1] + (0 if int(av) == int(bv) else 1),
            )
        prev = cur
    return int(prev[-1])


def nearest_codeword_distance(block: Sequence[int], feasible_codewords: Sequence[Sequence[int]]) -> int:
    return min(edit_distance(block, codeword) for codeword in feasible_codewords)


def quantile(values: Sequence[float], q: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(float(x) for x in values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def flatten(items: Iterable[Sequence[int]]) -> List[int]:
    return [int(x) for item in items for x in item]


def maybe_save_plots(summary_df: pd.DataFrame, output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("[warning] matplotlib is unavailable; skipping calibration plots.")
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(summary_df["logit_bias"], summary_df["mean_valid_block_fraction"], marker="o")
    ax.set_xlabel("logit_bias")
    ax.set_ylabel("mean_valid_block_fraction")
    ax.set_title("ECC Clean Validity vs Logit Bias")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "mean_valid_block_fraction.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(summary_df["logit_bias"], summary_df["q95_nearest_codeword_edit_distance"], marker="o")
    ax.set_xlabel("logit_bias")
    ax.set_ylabel("q95 nearest-codeword edit distance")
    ax.set_title("Clean Structural Deviation vs Logit Bias")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "q95_nearest_codeword_edit_distance.png", dpi=160)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    prompts = load_prompts(args.prompt_file, prompt_count=10)
    model_config = ModelConfig(
        backend=args.backend,
        model_name=args.model_name,
        device=args.device,
        use_4bit=args.use_4bit,
        mock_vocab_size=220,
    )
    model = build_language_model(model_config, corpus_texts=prompts)
    ecc_config = ECCConfig()
    partition = build_vocabulary_partition(model, prompts, ecc_config)
    generator = EccGenerator(model, partition, ecc_config)

    sequence_rows = []
    block_rows = []
    for bias in LOGIT_BIASES:
        setting = GenerationSetting(
            scheme="ecc",
            watermark_mode="soft",
            adaptive=not args.non_adaptive,
            target_blocks=args.target_blocks,
            max_new_tokens=args.max_new_tokens,
            seed=args.seed + int(bias * 100),
            logit_bias=float(bias),
        )
        generated = generator.generate_many(prompts, setting)
        for seq_idx, result in enumerate(generated):
            closed_blocks = result.decoded_clean.get("blocks_closed_by_boundary", [])
            valid_blocks = result.decoded_clean.get("valid_blocks", [])
            distances = [
                nearest_codeword_distance(block, generator.codebook.feasible)
                for block in closed_blocks
            ]
            num_valid_blocks = len(valid_blocks)
            valid_fraction = num_valid_blocks / args.target_blocks if args.target_blocks > 0 else math.nan
            sequence_rows.append(
                {
                    "sequence_index": seq_idx,
                    "logit_bias": bias,
                    "prompt": result.prompt,
                    "suffix_text": result.suffix_text,
                    "target_blocks": args.target_blocks,
                    "completed_blocks_runtime": result.runtime_state.completed_blocks,
                    "num_closed_blocks": result.decoded_clean.get("num_closed_blocks", len(closed_blocks)),
                    "num_clean_valid_blocks": num_valid_blocks,
                    "valid_block_fraction": valid_fraction,
                    "usable_sequence": int(num_valid_blocks > 0),
                    "nearest_codeword_edit_distances": json.dumps(distances),
                    "mean_nearest_codeword_edit_distance": mean(distances) if distances else math.nan,
                    "max_nearest_codeword_edit_distance": max(distances) if distances else math.nan,
                }
            )
            for block_idx, (block, dist) in enumerate(zip(closed_blocks, distances)):
                block_rows.append(
                    {
                        "sequence_index": seq_idx,
                        "logit_bias": bias,
                        "block_index": block_idx,
                        "block_length": len(block),
                        "block_bits": "".join(str(int(x)) for x in block),
                        "is_valid_codeword": int(len(block) == generator.codebook.block_len and tuple(block) in generator.codebook.feasible_set),
                        "nearest_codeword_edit_distance": dist,
                    }
                )
        print(f"Completed logit_bias={bias}: {len(generated)} sequences")

    sequence_df = pd.DataFrame(sequence_rows)
    block_df = pd.DataFrame(block_rows)
    summary_rows = []
    for bias in LOGIT_BIASES:
        seq_subset = sequence_df[sequence_df["logit_bias"] == bias]
        block_subset = block_df[block_df["logit_bias"] == bias]
        distances = block_subset["nearest_codeword_edit_distance"].tolist()
        summary_rows.append(
            {
                "logit_bias": bias,
                "num_sequences": len(seq_subset),
                "usable_sequence_rate": float(seq_subset["usable_sequence"].mean()) if not seq_subset.empty else math.nan,
                "mean_valid_blocks_per_sequence": float(seq_subset["num_clean_valid_blocks"].mean()) if not seq_subset.empty else math.nan,
                "mean_valid_block_fraction": float(seq_subset["valid_block_fraction"].mean()) if not seq_subset.empty else math.nan,
                "mean_nearest_codeword_edit_distance": float(mean(distances)) if distances else math.nan,
                "median_nearest_codeword_edit_distance": float(median(distances)) if distances else math.nan,
                "q90_nearest_codeword_edit_distance": quantile(distances, 0.90),
                "q95_nearest_codeword_edit_distance": quantile(distances, 0.95),
                "max_nearest_codeword_edit_distance": max(distances) if distances else math.nan,
                "num_closed_blocks": len(distances),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    sequence_df.to_csv(output_dir / "bias_clean_sequences.csv", index=False)
    block_df.to_csv(output_dir / "bias_clean_blocks.csv", index=False)
    summary_df.to_csv(output_dir / "bias_clean_summary.csv", index=False)
    maybe_save_plots(summary_df, output_dir)

    metadata = {
        "prompt_file": str((PROJECT_ROOT / args.prompt_file).resolve() if not Path(args.prompt_file).is_absolute() else Path(args.prompt_file)),
        "prompt_count": len(prompts),
        "logit_biases": LOGIT_BIASES,
        "backend": args.backend,
        "model_name": args.model_name,
        "requested_device": args.device,
        "resolved_device": getattr(model, "resolved_device", args.device),
        "use_4bit_requested": args.use_4bit,
        "quantization_mode": getattr(model, "quantization_mode", "none"),
        "adaptive": not args.non_adaptive,
        "target_blocks": args.target_blocks,
        "max_new_tokens": args.max_new_tokens,
        "seed": args.seed,
    }
    (output_dir / "sweep_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nSaved sweep outputs:")
    print(output_dir / "bias_clean_sequences.csv")
    print(output_dir / "bias_clean_blocks.csv")
    print(output_dir / "bias_clean_summary.csv")
    print(output_dir / "sweep_metadata.json")


if __name__ == "__main__":
    main()
