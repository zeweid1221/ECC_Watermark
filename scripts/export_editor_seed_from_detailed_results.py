#!/usr/bin/env python
"""Export exact-token ECC generations into the LLM editor seed schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--detailed-results", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--setting-key", default="ecc_soft_adaptive_bias5")
    parser.add_argument("--target-blocks", type=int, default=18)
    parser.add_argument("--expected-invalid-prefix-policy", default=None)
    return parser.parse_args()


def find_setting(payload: Dict[str, Any], setting_key: str) -> Dict[str, Any]:
    matches = [
        setting
        for setting in payload.get("settings", [])
        if setting.get("setting_key") == setting_key
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one setting_key={setting_key!r}; found {len(matches)}."
        )
    return matches[0]


def export_rows(setting: Dict[str, Any], target_blocks: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for sequence_index, generated in enumerate(setting.get("generated", [])):
        token_ids = [int(value) for value in generated.get("generated_token_ids", [])]
        bucket_ids = [int(value) for value in generated.get("generated_bucket_seq", [])]
        blocks = [
            [int(bit) for bit in block]
            for block in generated.get("generation_time_blocks", [])[:target_blocks]
        ]
        if not token_ids or len(token_ids) != len(bucket_ids):
            raise RuntimeError(
                f"sequence_index={sequence_index}: generated token/bucket lengths do not match."
            )
        if len(blocks) != target_blocks:
            raise RuntimeError(
                f"sequence_index={sequence_index}: expected {target_blocks} closed blocks, "
                f"found {len(blocks)}."
            )
        rows.append(
            {
                "sequence_index": sequence_index,
                "sample_index": sequence_index,
                "setting_key": setting.get("setting_key"),
                "logit_bias": setting.get("logit_bias"),
                "adaptive": setting.get("adaptive"),
                "adaptive_invalid_prefix_policy": setting.get(
                    "adaptive_invalid_prefix_policy", "legacy_unconstrained"
                ),
                "prompt": generated.get("prompt", ""),
                "suffix_text": generated.get("suffix_text", ""),
                "generated_token_ids": json.dumps(token_ids),
                "bucket_id_sequence": json.dumps(bucket_ids),
                "block_bucket_sequences_json": json.dumps(blocks),
                "stop_reason": generated.get("stop_reason"),
                "num_closed_blocks": generated.get("num_closed_blocks"),
                "num_feasible_closed_blocks": generated.get("num_feasible_closed_blocks"),
            }
        )
    if not rows:
        raise RuntimeError("The selected setting contains no generated samples.")
    return rows


def main() -> None:
    args = parse_args()
    detailed_path = Path(args.detailed_results)
    output_path = Path(args.output_csv)
    payload = json.loads(detailed_path.read_text(encoding="utf-8"))
    setting = find_setting(payload, args.setting_key)
    actual_policy = setting.get(
        "adaptive_invalid_prefix_policy", "legacy_unconstrained"
    )
    if (
        args.expected_invalid_prefix_policy is not None
        and actual_policy != args.expected_invalid_prefix_policy
    ):
        raise RuntimeError(
            f"Expected invalid-prefix policy {args.expected_invalid_prefix_policy!r}, "
            f"found {actual_policy!r} in {args.setting_key!r}."
        )
    rows = export_rows(setting, args.target_blocks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(
        f"Saved {len(rows)} exact-token editor seeds from {args.setting_key} "
        f"to {output_path}"
    )


if __name__ == "__main__":
    main()
