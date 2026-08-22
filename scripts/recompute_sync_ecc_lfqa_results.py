"""Replay saved sync-ECC LFQA attacks with the current detector.

Generation and perplexity are immutable inputs. The script reconstructs the
original deterministic attacks, verifies them against the saved row-level
artifacts, and recomputes detection/localization metrics without model weights.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd
from transformers import AutoTokenizer

try:
    from numba import njit
except ImportError:  # pragma: no cover - reference implementation remains available
    njit = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baselines.sync_ecc import (  # noqa: E402
    SyncEccConfig,
    SyncAlignmentResult,
    SyncEccSchedule,
    SyncEccWatermark,
    aggregate_sync_rows,
    apply_sync_attacks,
    evaluate_sync_blocks,
)
from watermark_project.config import GenerationProtocolConfig  # noqa: E402


_WORKER_DETECTOR: SyncEccWatermark | None = None


def _align_arrays_impl(
    observed_base_buckets: np.ndarray,
    implied_sync: np.ndarray,
    expected_sync: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    observed_length = len(observed_base_buckets)
    expected_length = len(expected_sync)
    dp = np.full((observed_length + 1, expected_length + 1), 10**9, dtype=np.int32)
    back = np.full((observed_length + 1, expected_length + 1), -1, dtype=np.int8)
    dp[0, 0] = 0
    for row in range(1, observed_length + 1):
        dp[row, 0] = row
        back[row, 0] = 1
    for col in range(1, expected_length + 1):
        dp[0, col] = col
        back[0, col] = 2
    for row in range(1, observed_length + 1):
        base_bucket = observed_base_buckets[row - 1]
        for col in range(1, expected_length + 1):
            best = dp[row - 1, col] + 1
            move = 1
            deletion = dp[row, col - 1] + 1
            if deletion < best:
                best = deletion
                move = 2
            if implied_sync[base_bucket, col - 1] == expected_sync[col - 1]:
                diagonal = dp[row - 1, col - 1]
                if diagonal <= best:
                    best = diagonal
                    move = 0
            dp[row, col] = best
            back[row, col] = move

    mapping = np.full(observed_length, -1, dtype=np.int32)
    insertion_reversed = np.empty(observed_length, dtype=np.int32)
    deletion_reversed = np.empty(expected_length, dtype=np.int32)
    insertion_count = 0
    deletion_count = 0
    row = observed_length
    col = expected_length
    while row > 0 or col > 0:
        move = back[row, col]
        if move == 0:
            mapping[row - 1] = col - 1
            row -= 1
            col -= 1
        elif move == 1:
            insertion_reversed[insertion_count] = row - 1
            insertion_count += 1
            row -= 1
        elif move == 2:
            deletion_reversed[deletion_count] = col - 1
            deletion_count += 1
            col -= 1
        else:
            raise RuntimeError("Synchronization alignment backtracking failed.")
    insertions = insertion_reversed[:insertion_count][::-1].copy()
    deletions = deletion_reversed[:deletion_count][::-1].copy()
    return mapping, insertions, deletions, int(dp[observed_length, expected_length])


_align_arrays = njit(cache=True)(_align_arrays_impl) if njit is not None else _align_arrays_impl


def accelerated_align(
    schedule: SyncEccSchedule,
    observed_token_ids: list[int],
    expected_length: int,
) -> SyncAlignmentResult:
    expected_length = int(expected_length)
    implied_sync = np.empty((schedule.config.bucket_count, expected_length), dtype=np.int16)
    expected_sync = np.empty(expected_length, dtype=np.int16)
    for step in range(expected_length):
        permutation = schedule.bucket_permutation(step)
        expected_sync[step] = schedule.sync_symbol(step)
        for base_bucket, step_bucket in enumerate(permutation):
            implied_sync[base_bucket, step] = int(step_bucket) % schedule.config.sigma_size
    observed = np.asarray(observed_token_ids, dtype=np.int64)
    observed_base = schedule.base_bucket_ids[observed].astype(np.int16)
    mapping, insertions, deletions, distance = _align_arrays(
        observed_base,
        implied_sync,
        expected_sync,
    )
    return SyncAlignmentResult(
        observed_to_expected=[int(value) for value in mapping],
        insertion_observed_indices=[int(value) for value in insertions],
        deletion_expected_positions=[int(value) for value in deletions],
        distance=int(distance),
    )


class _AcceleratedWatermark(SyncEccWatermark):
    def align(self, observed_token_ids: list[int], expected_length: int) -> SyncAlignmentResult:
        return accelerated_align(self.schedule, observed_token_ids, expected_length)


def _initialize_detector(vocab_size: int, config_values: dict[str, Any]) -> None:
    global _WORKER_DETECTOR
    config = SyncEccConfig(**config_values)
    detector = SyncEccWatermark.__new__(SyncEccWatermark)
    detector.config = config
    detector.schedule = SyncEccSchedule(int(vocab_size), config)
    _WORKER_DETECTOR = detector


def _detect_worker(payload: tuple[list[int], int]) -> Any:
    if _WORKER_DETECTOR is None:
        raise RuntimeError("Detector worker was not initialized.")
    token_ids, expected_blocks = payload
    return _WORKER_DETECTOR.detect(token_ids, expected_blocks)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _parse_json_list(value: Any) -> list[int]:
    if isinstance(value, str):
        value = json.loads(value)
    return [int(item) for item in value]


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def replay_seed(
    generation_seed: int,
    sequence_index: int,
    edit_rate: float,
    attack_budget: int,
    attack_index: int,
) -> int:
    return (
        int(generation_seed)
        + int(sequence_index)
        + int(float(edit_rate) * 1000)
        + 10000 * int(attack_budget)
        + 100000 * (int(attack_index) + 1)
    )


class _TokenizerModel:
    """Tokenizer-only surface used to recreate the generation-time ban mask."""

    def __init__(self, tokenizer: Any):
        self.tokenizer = tokenizer

    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)

    @property
    def all_special_ids(self) -> list[int]:
        return [int(value) for value in self.tokenizer.all_special_ids]

    def token_surface(self, token_id: int) -> str:
        return self.tokenizer.decode([int(token_id)], skip_special_tokens=False)


def _save_frame(frame: pd.DataFrame, stem: Path) -> None:
    frame.to_csv(stem.with_suffix(".csv"), index=False)
    frame.to_json(stem.with_suffix(".json"), orient="records", indent=2)
    try:
        frame.to_parquet(stem.with_suffix(".parquet"), index=False)
    except (ImportError, ModuleNotFoundError):
        pass


def _aggregate_setting(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    aggregate = aggregate_sync_rows(rows)
    return {
        **aggregate,
        "mean_realized_edits": float(np.mean([row["realized_edits"] for row in rows])),
    }


def _paper_summary(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (bias, attack_type), group in summary.groupby(
        ["logit_bias", "attack_type"], sort=True
    ):
        tp = int(group["TP"].sum())
        fp = int(group["FP"].sum())
        fn = int(group["FN"].sum())
        tn = int(group["TN"].sum())
        events = int(group["candidate_events"].sum())
        covered = int(group["candidate_events_covered"].sum())
        nonempty = int(group["candidate_nonempty_sets"].sum())
        candidate_size = int(group["candidate_total_size"].sum())
        rows.append(
            {
                "logit_bias": float(bias),
                "attack_type": str(attack_type),
                "protocol_scope": (
                    "native_indel" if attack_type in {"insert", "delete"} else "stress_test"
                ),
                "settings_aggregated": len(group),
                "block_tpr_micro": tp / (tp + fn) if tp + fn else 0.0,
                "block_far_micro": fp / (fp + tn) if fp + tn else 0.0,
                "candidate_coverage_micro": covered / events if events else 0.0,
                "mean_candidate_set_size_micro": (
                    candidate_size / nonempty if nonempty else 0.0
                ),
                "ppl_conditional_token_ids": float(
                    group["ppl_conditional_token_ids"].iloc[0]
                ),
                "ppl_unconditional_token_ids": float(
                    group["ppl_unconditional_token_ids"].iloc[0]
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--limit-settings", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    source = Path(args.result_dir).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    required = [
        source / "config.json",
        source / "generated.json",
        source / "details.csv",
        source / "summary.csv",
    ]
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(path)

    config = json.loads((source / "config.json").read_text(encoding="utf-8"))
    run_args = config["args"]
    generated = json.loads((source / "generated.json").read_text(encoding="utf-8"))
    old_details = pd.read_csv(source / "details.csv")
    old_summary = pd.read_csv(source / "summary.csv")
    setting_columns = [
        "logit_bias",
        "attack_type",
        "edit_rate",
        "attack_max_edits_per_block",
    ]
    settings = old_summary[setting_columns].to_dict("records")
    if args.limit_settings is not None:
        settings = settings[: int(args.limit_settings)]

    tokenizer = AutoTokenizer.from_pretrained(
        run_args["model_name"],
        use_fast=True,
        trust_remote_code=True,
        local_files_only=bool(args.local_files_only),
    )
    model = _TokenizerModel(tokenizer)
    protocol_values = dict(config["protocol"])
    protocol = GenerationProtocolConfig(**protocol_values)
    sync_config = SyncEccConfig(**config["sync_ecc_config"])
    method = _AcceleratedWatermark(model, sync_config, protocol)
    special_ids = set(model.all_special_ids)
    attack_vocab_ids = [
        token_id
        for token_id in range(model.vocab_size)
        if token_id not in special_ids and not method.ban_mask[token_id]
    ]
    if np.bincount(
        method.schedule.base_bucket_ids.astype(np.int64),
        minlength=sync_config.bucket_count,
    ).tolist() != config["base_bucket_counts"]:
        raise RuntimeError("Reconstructed keyed vocabulary partition does not match config.json.")

    generated_by_key = {
        (float(row["logit_bias"]), int(row["sequence_index"])): row
        for row in generated
    }
    reference_checks = 0
    for row in generated[:8]:
        fast = method.align(row["generated_token_ids"], int(run_args["target_blocks"]) * sync_config.block_len)
        reference_detector = SyncEccWatermark.__new__(SyncEccWatermark)
        reference_detector.config = sync_config
        reference_detector.schedule = method.schedule
        reference = reference_detector.align(
            row["generated_token_ids"],
            int(run_args["target_blocks"]) * sync_config.block_len,
        )
        if fast != reference:
            raise RuntimeError("Accelerated alignment does not match the reference implementation.")
        reference_checks += 1
    clean_by_key: dict[tuple[float, int], Any] = {}
    for key, row in generated_by_key.items():
        clean_by_key[key] = method.detect(
            row["generated_token_ids"],
            int(run_args["target_blocks"]),
        )

    corrected_rows: list[dict[str, Any]] = []
    replay_checks = 0
    executor = None
    if int(args.workers) > 1:
        executor = ProcessPoolExecutor(
            max_workers=int(args.workers),
            initializer=_initialize_detector,
            initargs=(model.vocab_size, asdict(sync_config)),
        )
    try:
        for setting_number, setting in enumerate(settings, start=1):
            mask = np.ones(len(old_details), dtype=bool)
            for column, value in setting.items():
                mask &= old_details[column].to_numpy() == value
            saved_rows = old_details.loc[mask].sort_values("sequence_index")
            if len(saved_rows) != int(run_args["num_samples"]):
                raise RuntimeError(f"Incomplete saved setting: {setting}")
            attack_type = str(setting["attack_type"])
            attack_index = list(run_args["attack_types"]).index(attack_type)
            replay_items = []
            for saved in saved_rows.to_dict("records"):
                sequence_index = int(saved["sequence_index"])
                key = (float(setting["logit_bias"]), sequence_index)
                generation = generated_by_key[key]
                tokens = [int(value) for value in generation["generated_token_ids"]]
                block_len = int(run_args["block_len"])
                token_blocks = [
                    tokens[start : start + block_len]
                    for start in range(0, len(tokens), block_len)
                ]
                attacked = apply_sync_attacks(
                    token_blocks,
                    edit_rate=float(setting["edit_rate"]),
                    max_edits_per_block=int(setting["attack_max_edits_per_block"]),
                    edit_count_mode=str(run_args["edit_count_mode"]),
                    attack_type=attack_type,
                    vocab_ids=attack_vocab_ids,
                    schedule=method.schedule,
                    rng=random.Random(
                        replay_seed(
                            int(run_args["generation_seed"]),
                            sequence_index,
                            float(setting["edit_rate"]),
                            int(setting["attack_max_edits_per_block"]),
                            attack_index,
                        )
                    ),
                    strict_interior_insertions=bool(run_args["strict_interior_insertions"]),
                )
                replay_items.append((saved, key, attacked))
            detection_inputs = [
                (item[2].observed_token_ids, int(run_args["target_blocks"]))
                for item in replay_items
            ]
            detections = (
                list(executor.map(_detect_worker, detection_inputs, chunksize=4))
                if executor is not None
                else [method.detect(*item) for item in detection_inputs]
            )
            for (saved, key, attacked), detection in zip(replay_items, detections):
                sequence_index = int(saved["sequence_index"])
                expected_gt = _parse_json_list(saved["gt_blocks"])
                if attacked.gt_blocks != expected_gt:
                    raise RuntimeError(
                        f"GT replay mismatch for setting {setting}, sequence {sequence_index}."
                    )
                if attacked.realized_edits != int(saved["realized_edits"]):
                    raise RuntimeError(
                        f"Edit-count replay mismatch for setting {setting}, sequence {sequence_index}."
                    )
                if detection.alignment.distance != int(saved["alignment_distance"]):
                    raise RuntimeError(
                        f"Alignment replay mismatch for setting {setting}, sequence {sequence_index}."
                    )
                replay_checks += 1
                evaluation = evaluate_sync_blocks(
                    detection,
                    attacked.gt_events_per_block,
                    int(run_args["target_blocks"]),
                    candidate_tolerance=int(run_args["candidate_tolerance"]),
                )
                clean = clean_by_key[key]
                corrected_rows.append(
                    {
                        **{
                            column: saved[column]
                            for column in old_details.columns
                            if column
                            not in {
                                "clean_predicted_blocks",
                                "alignment_distance",
                                "alignment_blocks",
                                "vt_inconsistent_blocks",
                                "candidate_positions",
                                "candidate_events_by_block",
                                "gt_blocks",
                                "pred_blocks",
                                "TP",
                                "FP",
                                "FN",
                                "TN",
                                "block_tpr",
                                "block_far",
                                "candidate_events",
                                "candidate_events_covered",
                                "candidate_coverage",
                                "candidate_nonempty_sets",
                                "candidate_total_size",
                                "mean_candidate_set_size",
                            }
                        },
                        "clean_predicted_blocks": _json(clean.predicted_blocks),
                        "alignment_distance": detection.alignment.distance,
                        "alignment_blocks": _json(detection.alignment_blocks),
                        "vt_inconsistent_blocks": _json(detection.vt_inconsistent_blocks),
                        "candidate_positions": _json(detection.candidate_positions),
                        "candidate_events_by_block": _json(detection.candidate_events_by_block),
                        "gt_blocks": _json(evaluation["gt_blocks"]),
                        "pred_blocks": _json(evaluation["pred_blocks"]),
                        **{
                            metric: evaluation[metric]
                            for metric in (
                                "TP",
                                "FP",
                                "FN",
                                "TN",
                                "block_tpr",
                                "block_far",
                                "candidate_events",
                                "candidate_events_covered",
                                "candidate_coverage",
                                "candidate_nonempty_sets",
                                "candidate_total_size",
                                "mean_candidate_set_size",
                            )
                        },
                    }
                )
            print(f"[{setting_number}/{len(settings)}] replayed {setting}", flush=True)
    finally:
        if executor is not None:
            executor.shutdown()

    corrected_details = pd.DataFrame(corrected_rows)
    summary_rows: list[dict[str, Any]] = []
    for setting in settings:
        mask = np.ones(len(corrected_details), dtype=bool)
        for column, value in setting.items():
            mask &= corrected_details[column].to_numpy() == value
        rows = corrected_details.loc[mask].to_dict("records")
        old_row_mask = np.ones(len(old_summary), dtype=bool)
        for column, value in setting.items():
            old_row_mask &= old_summary[column].to_numpy() == value
        base = old_summary.loc[old_row_mask].iloc[0].to_dict()
        base.update(_aggregate_setting(rows))
        bias = float(setting["logit_bias"])
        clean_counts = [
            len(clean_by_key[(bias, sequence_index)].predicted_blocks)
            for sequence_index in range(int(run_args["num_samples"]))
        ]
        base["mean_clean_flagged_blocks"] = float(np.mean(clean_counts))
        base["detector_protocol"] = "accepted_restored_block_length_v1"
        summary_rows.append(base)
    corrected_summary = pd.DataFrame(summary_rows)

    _save_frame(corrected_details, output / "details_corrected")
    _save_frame(corrected_summary, output / "summary_corrected")
    paper_summary = _paper_summary(corrected_summary)
    paper_summary.to_csv(output / "paper_summary_corrected.csv", index=False)
    report = {
        "status": "passed",
        "source_result_dir": str(source),
        "source_files_sha256": {path.name: _sha256(path) for path in required},
        "implementation_git_commit": _git_commit(),
        "recompute_script_sha256": _sha256(Path(__file__).resolve()),
        "sync_ecc_config": asdict(sync_config),
        "detector_protocol": "accepted_restored_block_length_v1",
        "alarm_rule": "restored block token count != block_len",
        "insertion_assignment": "previous matched block, otherwise next matched block",
        "attack_replay": "deterministic from saved generations and config",
        "attack_vocab_size": len(attack_vocab_ids),
        "replay_rows_checked": replay_checks,
        "accelerated_alignment_reference_checks": reference_checks,
        "workers": int(args.workers),
        "replay_fields_checked": ["realized_edits", "gt_blocks", "alignment_distance"],
        "generation_and_ppl_reused_unchanged": True,
        "summary_rows": len(corrected_summary),
        "detail_rows": len(corrected_details),
        "paper_summary_rows": len(paper_summary),
    }
    (output / "recompute_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
