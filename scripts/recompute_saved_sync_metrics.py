"""Recompute accepted sync-ECC block metrics from saved readable artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baselines.sync_ecc import assign_insertions_to_neighbor_block  # noqa: E402


def _trim_length(token_ids: Sequence[int], pad_id: int) -> int:
    length = len(token_ids)
    while length and int(token_ids[length - 1]) == int(pad_id):
        length -= 1
    return length


def _block_lengths(
    token_ids: Sequence[int],
    block_ids: Sequence[int],
    num_blocks: int,
) -> list[int]:
    lengths = [0] * int(num_blocks)
    for _, block_id in zip(token_ids, block_ids):
        block_id = int(block_id)
        if 0 <= block_id < int(num_blocks):
            lengths[block_id] += 1
    return lengths


def recompute_metrics(data: dict[str, Any], alignment: dict[str, Any], pad_id: int) -> dict[str, Any]:
    edited = data["tokd_edited_suffix"]
    gt_blocks = data["gt_block_full"]
    predicted_blocks = alignment["block_id_hat"]
    distances = alignment["dist"]
    block_len = int(data["block_len"])
    expected_length = int(data["suffixes__token_count"])
    num_blocks = (expected_length + block_len - 1) // block_len
    tp = fp = fn = tn = 0
    rows = []

    for row_index in range(int(edited.shape[0])):
        tokens = edited[row_index].tolist()
        length = _trim_length(tokens, pad_id)
        tokens = tokens[:length]
        gt_ids = [int(value) for value in gt_blocks[row_index, :length].tolist()]
        raw_pred_ids = [int(value) for value in predicted_blocks[row_index, :length].tolist()]
        pred_ids = assign_insertions_to_neighbor_block(raw_pred_ids)
        gt_lengths = _block_lengths(tokens, gt_ids, num_blocks)
        pred_lengths = _block_lengths(tokens, pred_ids, num_blocks)
        gt_flags = [value != block_len for value in gt_lengths]
        pred_flags = [value != block_len for value in pred_lengths]
        row_tp = sum(int(g and p) for g, p in zip(gt_flags, pred_flags))
        row_fn = sum(int(g and not p) for g, p in zip(gt_flags, pred_flags))
        row_fp = sum(int(not g and p) for g, p in zip(gt_flags, pred_flags))
        row_tn = sum(int(not g and not p) for g, p in zip(gt_flags, pred_flags))
        tp += row_tp
        fn += row_fn
        fp += row_fp
        tn += row_tn
        rows.append(
            {
                "sequence_index": row_index,
                "TP": row_tp,
                "FP": row_fp,
                "FN": row_fn,
                "TN": row_tn,
                "alignment_distance": int(distances[row_index]),
                "gt_flagged_blocks": [index for index, flag in enumerate(gt_flags) if flag],
                "pred_flagged_blocks": [index for index, flag in enumerate(pred_flags) if flag],
            }
        )

    return {
        "protocol": "accepted_sync_ecc_restored_block_length_v1",
        "alarm_rule": "restored block token count != block_len",
        "insertion_assignment": "previous matched block, otherwise next matched block",
        "num_sequences": int(edited.shape[0]),
        "num_blocks_per_sequence": int(num_blocks),
        "block_len": int(block_len),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "block_tpr": float(tp / (tp + fn)) if tp + fn else 0.0,
        "block_far": float(fp / (fp + tn)) if fp + tn else 0.0,
        "mean_alignment_distance": float(np.mean(np.asarray(distances, dtype=np.float64))),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-dir", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    root = Path(args.evaluation_dir).resolve()
    data = torch.load(root / "data.pt", map_location="cpu", weights_only=False)
    alignment = torch.load(root / "sync_alignment_out.pt", map_location="cpu", weights_only=False)
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    metrics = recompute_metrics(data, alignment, int(meta["pad_id"]))
    output = Path(args.output).resolve() if args.output else root / "readable_recompute_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: value for key, value in metrics.items() if key != "rows"}, indent=2))
    print(f"Saved per-sequence results to {output}")


if __name__ == "__main__":
    main()
