from __future__ import annotations

import argparse
import json
import math
import sys
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

try:
    from transformers import AutoTokenizer
except Exception:  # pragma: no cover
    AutoTokenizer = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:  # noqa: E402
    from scripts.preview_watermarked_generation_quality import load_prompt_lines
except ModuleNotFoundError:  # Direct execution adds scripts/ rather than the project root package.
    from preview_watermarked_generation_quality import load_prompt_lines
from watermark_project.config import ModelConfig  # noqa: E402
from watermark_project.ecc_detector import EccCodebook  # noqa: E402
from watermark_project.io_utils import ensure_dir, save_dataframe, write_json  # noqa: E402
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile  # noqa: E402
from watermark_project.modeling import MockLanguageModel, clean_text  # noqa: E402
from watermark_project.partitioning import (  # noqa: E402
    load_vocabulary_partition,
    validate_vocabulary_partition,
)


class TokenizerOnlyModel:
    def __init__(self, model_name: str, *, local_files_only: bool = False) -> None:
        if AutoTokenizer is None:
            raise RuntimeError("transformers is required for --backend hf.")
        self.config = ModelConfig(backend="hf", model_name=model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=True,
            local_files_only=local_files_only,
            # Final text is an ordinary string. A literal sequence such as
            # "</s>" must not be reinterpreted as a tokenizer control token.
            split_special_tokens=True,
        )

    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)

    @property
    def all_special_ids(self) -> Sequence[int]:
        return [int(x) for x in self.tokenizer.all_special_ids]

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        return [
            int(x)
            for x in self.tokenizer.encode(
                text,
                add_special_tokens=add_special_tokens,
            )
        ]

    def token_surface(self, token_id: int) -> str:
        return self.tokenizer.decode([int(token_id)], skip_special_tokens=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Final-text-only ECC global watermark verification and ROC evaluation."
    )
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--partition-dir", required=True)
    parser.add_argument("--backend", choices=["mock", "hf"], default="hf")
    parser.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--partition-prompt-file", default=None)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="label")
    parser.add_argument("--source-column", default="source_type")
    parser.add_argument("--id-column", default="sample_id")
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--tolerance", type=int, default=0)
    parser.add_argument("--expected-blocks", type=int, default=None)
    parser.add_argument(
        "--phase-mode",
        choices=["start_aligned", "best_phase"],
        default="best_phase",
        help=(
            "Use phase 0 when the beginning of the watermarked answer is known, or scan all "
            "serialized-block phases for an excerpt-style verifier."
        ),
    )
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--require-semantic-partition", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    profile = get_model_profile(args.model_profile) if args.model_profile else None
    if profile and args.model_name and args.model_name != profile.model_name:
        parser.error(
            f"--model-profile {profile.key} requires --model-name {profile.model_name!r}."
        )
    args.model_name = args.model_name or (
        profile.model_name if profile else ("mock-lm" if args.backend == "mock" else None)
    )
    if not args.model_name:
        parser.error("--model-name or --model-profile is required for --backend hf.")
    return args


def build_tokenizer_model(args: argparse.Namespace, texts: Sequence[str]):
    if args.backend == "hf":
        return TokenizerOnlyModel(
            args.model_name,
            local_files_only=args.local_files_only,
        )
    corpus = (
        load_prompt_lines(args.partition_prompt_file)
        if args.partition_prompt_file
        else [clean_text(text) for text in texts]
    )
    return MockLanguageModel(
        ModelConfig(
            backend="mock",
            model_name=args.model_name,
            mock_vocab_size=256,
        ),
        corpus_texts=corpus,
    )


def map_final_text_to_structure(text: str, model, partition) -> tuple[List[int], List[int]]:
    token_ids = [int(x) for x in model.encode(text, add_special_tokens=False)]
    structural_sequence: List[int] = []
    for token_id in token_ids:
        if token_id < 0 or token_id >= len(partition.token_to_bucket):
            raise ValueError(f"out_of_range_token_id:{token_id}")
        bucket = int(partition.token_to_bucket[token_id])
        if bucket not in (0, 1, 2):
            raise ValueError(f"excluded_token_id:{token_id}")
        structural_sequence.append(bucket)
    return token_ids, structural_sequence


def estimate_block_count(num_tokens: int, block_len: int) -> int:
    serialized_block_len = int(block_len) + 1
    return max(1, int(math.floor((int(num_tokens) / serialized_block_len) + 0.5)))


def build_payload_distance_lookup(
    codebook: EccCodebook,
) -> Dict[Tuple[int, ...], int]:
    lookup: Dict[Tuple[int, ...], int] = {}
    for payload in product((0, 1, 2), repeat=codebook.block_len):
        lookup[payload] = min(
            sum(int(obs) != int(ref) for obs, ref in zip(payload, codeword))
            for codeword in codebook.feasible
        )
    return lookup


def score_serialized_phase(
    structural_sequence: Sequence[int],
    *,
    phase: int,
    estimated_blocks: int,
    tolerance: int,
    codebook: EccCodebook,
    payload_distance_lookup: Dict[Tuple[int, ...], int],
) -> Dict[str, Any] | None:
    serialized_block_len = codebook.block_len + 1
    available = len(structural_sequence) - int(phase)
    num_blocks = available // serialized_block_len
    if num_blocks <= 0:
        return None

    block_costs: List[Dict[str, int]] = []
    for block_index in range(num_blocks):
        start = int(phase) + block_index * serialized_block_len
        segment = tuple(
            int(x)
            for x in structural_sequence[start : start + serialized_block_len]
        )
        payload = segment[: codebook.block_len]
        boundary = int(segment[-1])
        payload_distance = int(payload_distance_lookup[payload])
        boundary_cost = int(boundary != codebook.boundary_symbol)
        block_costs.append(
            {
                "block_index": block_index,
                "structural_start": start,
                "structural_end_exclusive": start + serialized_block_len,
                "payload_distance": payload_distance,
                "boundary_cost": boundary_cost,
                "total_distance": payload_distance + boundary_cost,
            }
        )

    consumed_end = int(phase) + num_blocks * serialized_block_len
    unmatched_symbol_cost = int(phase) + (len(structural_sequence) - consumed_end)
    block_count_mismatch_cost = abs(num_blocks - int(estimated_blocks))
    scored_block_distance = sum(item["total_distance"] for item in block_costs)
    raw_alignment_cost = (
        scored_block_distance
        + unmatched_symbol_cost
        + block_count_mismatch_cost
    )
    normalized_alignment_cost = raw_alignment_cost / max(1, int(estimated_blocks))
    consistent_count = sum(
        item["payload_distance"] <= int(tolerance)
        and item["boundary_cost"] == 0
        for item in block_costs
    )
    exact_count = sum(
        item["payload_distance"] == 0 and item["boundary_cost"] == 0
        for item in block_costs
    )
    denominator = max(1, num_blocks, int(estimated_blocks))
    return {
        "phase": int(phase),
        "num_blocks": num_blocks,
        "num_consistent_blocks": int(consistent_count),
        "num_exact_feasible_blocks": int(exact_count),
        "scored_block_distance": int(scored_block_distance),
        "unmatched_symbol_cost": int(unmatched_symbol_cost),
        "block_count_mismatch_cost": int(block_count_mismatch_cost),
        "raw_alignment_cost": int(raw_alignment_cost),
        "normalized_alignment_cost": float(normalized_alignment_cost),
        "global_score": float(1.0 / (1.0 + normalized_alignment_cost)),
        "tolerance_consistency_score": float(consistent_count / denominator),
        "exact_feasible_score": float(exact_count / denominator),
        "block_costs": block_costs,
    }


def verification_row(
    text: str,
    model,
    partition,
    codebook: EccCodebook,
    payload_distance_lookup: Dict[Tuple[int, ...], int],
    tolerance: int,
    expected_blocks: int | None,
    phase_mode: str,
) -> Dict[str, Any]:
    token_ids, structural_sequence = map_final_text_to_structure(text, model, partition)
    estimated_blocks = (
        int(expected_blocks)
        if expected_blocks is not None
        else estimate_block_count(len(token_ids), codebook.block_len)
    )
    block_count_source = "explicit_override" if expected_blocks is not None else "token_length_estimate"
    serialized_block_len = codebook.block_len + 1
    phases = (
        [0]
        if phase_mode == "start_aligned"
        else list(range(min(serialized_block_len, max(1, len(structural_sequence)))))
    )
    phase_scores = [
        score
        for phase in phases
        if (
            score := score_serialized_phase(
                structural_sequence,
                phase=phase,
                estimated_blocks=estimated_blocks,
                tolerance=tolerance,
                codebook=codebook,
                payload_distance_lookup=payload_distance_lookup,
            )
        )
        is not None
    ]
    if not phase_scores:
        raise ValueError("Text is too short to contain one serialized ECC block.")
    selected = min(
        phase_scores,
        key=lambda item: (
            item["raw_alignment_cost"],
            item["unmatched_symbol_cost"],
            -item["num_blocks"],
            item["phase"],
        ),
    )
    return {
        "num_token_ids": len(token_ids),
        "num_structural_symbols": len(structural_sequence),
        "num_boundary_symbols": sum(int(x) == codebook.boundary_symbol for x in structural_sequence),
        "num_scored_blocks": selected["num_blocks"],
        "estimated_blocks": estimated_blocks,
        "block_count_source": block_count_source,
        "selected_phase": selected["phase"],
        "num_consistent_blocks": selected["num_consistent_blocks"],
        "num_exact_feasible_blocks": selected["num_exact_feasible_blocks"],
        "scored_block_distance": selected["scored_block_distance"],
        "unmatched_symbol_cost": selected["unmatched_symbol_cost"],
        "block_count_mismatch_cost": selected["block_count_mismatch_cost"],
        "raw_alignment_cost": selected["raw_alignment_cost"],
        "normalized_alignment_cost": selected["normalized_alignment_cost"],
        "global_score": selected["global_score"],
        "tolerance_consistency_score": selected["tolerance_consistency_score"],
        "exact_feasible_score": selected["exact_feasible_score"],
        "parsed_block_costs_json": json.dumps(selected["block_costs"]),
        "phase_scores_json": json.dumps(
            [
                {
                    key: value
                    for key, value in score.items()
                    if key != "block_costs"
                }
                for score in phase_scores
            ]
        ),
        "token_ids_json": json.dumps(token_ids),
        "structural_sequence_json": json.dumps(structural_sequence),
    }


def binary_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    positives = [score for label, score in zip(labels, scores) if int(label) == 1]
    negatives = [score for label, score in zip(labels, scores) if int(label) == 0]
    if not positives or not negatives:
        return float("nan")
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def roc_rows(labels: Sequence[int], scores: Sequence[float]) -> List[Dict[str, float]]:
    thresholds = [math.inf] + sorted(set(float(x) for x in scores), reverse=True) + [-math.inf]
    rows: List[Dict[str, float]] = []
    for threshold in thresholds:
        predictions = [float(score) >= threshold for score in scores]
        tp = sum(int(label) == 1 and pred for label, pred in zip(labels, predictions))
        fp = sum(int(label) == 0 and pred for label, pred in zip(labels, predictions))
        fn = sum(int(label) == 1 and not pred for label, pred in zip(labels, predictions))
        tn = sum(int(label) == 0 and not pred for label, pred in zip(labels, predictions))
        rows.append(
            {
                "threshold": threshold,
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "TN": tn,
                "tpr": tp / (tp + fn) if tp + fn else 0.0,
                "fpr": fp / (fp + tn) if fp + tn else 0.0,
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    frame = pd.read_csv(args.input_csv)
    for column in (args.text_column, args.label_column):
        if column not in frame.columns:
            raise ValueError(f"Missing required input column {column!r}.")
    texts = frame[args.text_column].fillna("").astype(str).tolist()
    labels = [int(x) for x in frame[args.label_column].tolist()]
    if any(label not in (0, 1) for label in labels):
        raise ValueError("Labels must be binary 0/1.")

    model = build_tokenizer_model(args, texts)
    partition = load_vocabulary_partition(args.partition_dir)
    validate_vocabulary_partition(
        partition,
        model,
        require_semantic_split=args.require_semantic_partition,
    )
    codebook = EccCodebook(block_len=args.block_len, vt_a=args.vt_a)
    payload_distance_lookup = build_payload_distance_lookup(codebook)

    details: List[Dict[str, Any]] = []
    for row_index, (_, row) in enumerate(frame.iterrows()):
        metrics = verification_row(
            text=str(row[args.text_column]),
            model=model,
            partition=partition,
            codebook=codebook,
            payload_distance_lookup=payload_distance_lookup,
            tolerance=args.tolerance,
            expected_blocks=args.expected_blocks,
            phase_mode=args.phase_mode,
        )
        details.append(
            {
                "sample_id": row.get(args.id_column, row_index),
                "source_type": row.get(args.source_column, "unspecified"),
                "label": int(row[args.label_column]),
                "text": str(row[args.text_column]),
                **metrics,
            }
        )
    detail_df = pd.DataFrame(details)
    scores = detail_df["global_score"].astype(float).tolist()
    roc_df = pd.DataFrame(roc_rows(labels, scores))
    auc = binary_auc(labels, scores)
    source_summary = (
        detail_df.groupby(["source_type", "label"], dropna=False)
        .agg(
            num_samples=("label", "size"),
            mean_global_score=("global_score", "mean"),
            mean_normalized_alignment_cost=("normalized_alignment_cost", "mean"),
            mean_tolerance_consistency_score=("tolerance_consistency_score", "mean"),
            mean_exact_feasible_score=("exact_feasible_score", "mean"),
            mean_scored_blocks=("num_scored_blocks", "mean"),
            mean_estimated_blocks=("estimated_blocks", "mean"),
        )
        .reset_index()
    )
    summary = {
        "num_samples": len(detail_df),
        "num_positive": sum(labels),
        "num_negative": len(labels) - sum(labels),
        "roc_auc": auc,
        "score_definition": (
            "1 / (1 + normalized serialized-codeword distance), using a precomputed "
            "payload-to-codebook distance table and a final-text length-derived block count"
        ),
        "auxiliary_score_definition": (
            "tolerance-consistent serialized blocks / "
            "max(scored serialized blocks, estimated blocks, 1)"
        ),
        "source_summary": source_summary.to_dict(orient="records"),
    }
    save_dataframe(detail_df, str(Path(args.output_dir) / "global_verification_details"), save_parquet=False)
    save_dataframe(roc_df, str(Path(args.output_dir) / "global_verification_roc"), save_parquet=False)
    save_dataframe(source_summary, str(Path(args.output_dir) / "global_verification_summary_by_source"), save_parquet=False)
    write_json(str(Path(args.output_dir) / "global_verification_summary.json"), summary)
    write_json(
        str(Path(args.output_dir) / "global_verification_config.json"),
        {
            "args": vars(args),
            "deployment_pipeline": (
                "final text -> tokenizer ids -> fixed partition buckets "
                "-> serialized-block phase scan -> normalized global structural distance"
            ),
        },
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
