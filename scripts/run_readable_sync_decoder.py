"""Run the readable accepted sync-ECC alignment on a materialized data.pt."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baselines.sync_ecc import (  # noqa: E402
    SyncEccConfig,
    SyncEccSchedule,
    align_sync_tokens,
)


def _trim_length(token_ids: list[int], pad_id: int) -> int:
    length = len(token_ids)
    while length and int(token_ids[length - 1]) == int(pad_id):
        length -= 1
    return length


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-dir", required=True)
    parser.add_argument("--pad-id", required=True, type=int)
    args = parser.parse_args()

    root = Path(args.evaluation_dir).resolve()
    data = torch.load(root / "data.pt", map_location="cpu", weights_only=False)
    edited = data["tokd_edited_suffix"]
    expected_length = int(data["suffixes__token_count"])
    config = SyncEccConfig(
        block_len=int(data["block_len"]),
        sigma_size=int(data["sigma_size"]),
        vt_a=int(data["vt_a"]),
        seed=int(data["wm_seed"]),
        random_partition_each_step=bool(data["random_partition_each_step"]),
    )
    vocab_size = max(int(edited.max().item()) + 1, int(args.pad_id) + 1)
    schedule = SyncEccSchedule(vocab_size, config)
    alignments = []
    for row in edited:
        values = [int(value) for value in row.tolist()]
        values = values[: _trim_length(values, int(args.pad_id))]
        alignments.append(align_sync_tokens(schedule, values, expected_length))

    width = max(len(result.observed_to_expected) for result in alignments)
    t_hat = torch.full((len(alignments), width), -1, dtype=torch.long)
    block_ids = torch.full((len(alignments), width), -1, dtype=torch.long)
    for row_index, result in enumerate(alignments):
        length = len(result.observed_to_expected)
        mapping = torch.tensor(result.observed_to_expected, dtype=torch.long)
        t_hat[row_index, :length] = mapping
        block_ids[row_index, :length] = torch.where(
            mapping >= 0,
            mapping // int(config.block_len),
            torch.full_like(mapping, -1),
        )
    output = {
        "t_hat": t_hat,
        "block_id_hat": block_ids,
        "dist": torch.tensor([result.distance for result in alignments], dtype=torch.long),
        "block_len": int(config.block_len),
        "orig_suffix_len": int(expected_length),
        "sigma_size": int(config.sigma_size),
        "seed": int(config.seed),
        "random_partition_each_step": bool(config.random_partition_each_step),
        "prefix_len_effective": 0,
        "mode": "readable_pure_suffix_sync_alignment_insdel_only",
    }
    output_path = root / "sync_alignment_out.pt"
    torch.save(output, output_path)
    print(
        f"Aligned {len(alignments)} rows; mean distance="
        f"{sum(result.distance for result in alignments) / len(alignments):.6f}"
    )
    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
