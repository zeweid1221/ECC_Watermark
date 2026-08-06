from __future__ import annotations

from typing import Any, Dict, List, Sequence

try:
    from transformers import AutoTokenizer
except Exception:  # pragma: no cover
    AutoTokenizer = None

from .config import ModelConfig
from .ecc_detector import (
    EccCodebook,
    EccDecoderConfig,
    detect_sequence_multiple,
    parsed_block_exceeds_tolerance,
)
from .modeling import MockLanguageModel
from .partitioning import VocabularyPartition


class DeploymentTokenizerModel:
    def __init__(self, model_name: str) -> None:
        if AutoTokenizer is None:
            raise RuntimeError("transformers is required for an HF deployment tokenizer.")
        self.config = ModelConfig(backend="hf", model_name=model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    @property
    def vocab_size(self) -> int:
        return len(self.tokenizer)

    @property
    def all_special_ids(self) -> Sequence[int]:
        return [int(x) for x in self.tokenizer.all_special_ids]

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        return [
            int(x)
            for x in self.tokenizer.encode(text, add_special_tokens=add_special_tokens)
        ]

    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        return self.tokenizer.decode(
            [int(x) for x in token_ids],
            skip_special_tokens=skip_special_tokens,
        )

    def token_surface(self, token_id: int) -> str:
        return self.tokenizer.decode([int(token_id)], skip_special_tokens=False)


def build_deployment_tokenizer_model(
    backend: str,
    model_name: str,
    corpus_texts: Sequence[str] = (),
):
    if backend == "hf":
        return DeploymentTokenizerModel(model_name)
    if backend == "mock":
        return MockLanguageModel(
            ModelConfig(
                backend="mock",
                model_name=model_name,
                mock_vocab_size=256,
            ),
            corpus_texts=corpus_texts,
        )
    raise ValueError(f"Unsupported deployment tokenizer backend: {backend}")


def final_text_to_structural_sequence(
    text: str,
    model,
    partition: VocabularyPartition,
) -> tuple[List[int], List[int]]:
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


def reconstruct_detector_alignment_from_final_text(
    text: str,
    model,
    partition: VocabularyPartition,
    codebook: EccCodebook,
    decoder_config: EccDecoderConfig,
    tolerance: int,
) -> Dict[str, Any]:
    token_ids, structural_sequence = final_text_to_structural_sequence(
        text,
        model,
        partition,
    )
    pred_blocks = detect_sequence_multiple(
        structural_sequence,
        decoder_config=decoder_config,
        codebook=codebook,
    )
    details: List[Dict[str, Any]] = []
    spans: Dict[str, str] = {}
    token_block_map = [-1] * len(token_ids)
    for parsed_index, block in enumerate(pred_blocks):
        start = block.info.get("observed_span_start")
        end = block.info.get("observed_span_end_exclusive")
        if start is None or end is None:
            raise RuntimeError("detector_parse_missing_observed_span")
        start = max(0, int(start))
        end = max(start, min(int(end), len(token_ids)))
        boundary_index = block.info.get("observed_boundary_index")
        snippet_indices = list(range(start, end))
        for token_index in snippet_indices:
            token_block_map[token_index] = int(parsed_index)
        spans[str(parsed_index)] = (
            model.decode([token_ids[index] for index in snippet_indices], skip_special_tokens=True)
            if snippet_indices
            else ""
        )
        details.append(
            {
                "parsed_block_index": int(parsed_index),
                "exceeds_tolerance": bool(
                    parsed_block_exceeds_tolerance(
                        block,
                        tolerance=tolerance,
                        codebook=codebook,
                    )
                ),
                "observed_structural_span": {
                    "start": int(start),
                    "end_exclusive": int(end),
                },
                "observed_structural_segment": [
                    int(x) for x in structural_sequence[start:end]
                ],
                "observed_payload_tokens": [int(x) for x in block.block_tokens],
                "decoded_codeword": (
                    [int(x) for x in block.decoded_codeword]
                    if block.decoded_codeword is not None
                    else None
                ),
                "candidate_edit_locations": [
                    [str(kind), int(index)] for kind, index in block.candidates
                ],
                "is_boundary_edited": bool(block.is_boundary_edited),
                "boundary_edit_type": block.boundary_edit_type,
                "actual_boundary_following_index": (
                    int(boundary_index) if boundary_index is not None else None
                ),
                "payload_distance": block.info.get("payload_distance"),
                "total_distance": block.info.get("total_distance"),
                "boundary_state": block.info.get("boundary_state"),
            }
        )
    return {
        "edited_token_ids": token_ids,
        "edited_structural_sequence": structural_sequence,
        "pred_blocks_detailed": details,
        "detector_aligned_block_text_spans": spans,
        "edited_token_block_map_from_detector": token_block_map,
    }
