from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
from transformers import AutoTokenizer

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_llm_editor_experiment import (  # noqa: E402
    ValidatedInstruction,
    approx_text_match,
    build_block_text_spans,
    build_detector_aligned_block_text_spans,
    build_detector_block_details,
    build_edited_token_block_map,
    build_summary_dataframe,
    build_text_units_from_generated_tokens,
    build_token_block_map_from_units,
    build_token_bucket_ids_from_units,
    global_gap_to_block_offset,
    global_payload_pos_to_block_offset,
    load_seed_dataframe,
    local_window_for_index,
    parse_bucket_id_sequence,
    parse_optional_int_list,
    parse_payload_blocks_json,
    tokenize_new_content,
)
from watermark_project.config import ECCConfig  # noqa: E402
from watermark_project.ecc_detector import (  # noqa: E402
    EccCodebook,
    EccDecoderConfig,
    detect_sequence_multiple,
    evaluate_predictions_multiple,
    parsed_block_exceeds_tolerance,
)
from watermark_project.edits import EditEvent  # noqa: E402
from watermark_project.io_utils import ensure_dir, save_dataframe, write_json  # noqa: E402
from watermark_project.modeling import stable_hash_int  # noqa: E402
from watermark_project.partitioning import VocabularyPartition, load_vocabulary_partition  # noqa: E402


class TokenizerOnlyModel:
    def __init__(self, model_name: str) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.vocab_size = len(self.tokenizer)
        self.all_special_ids = [int(x) for x in self.tokenizer.all_special_ids]

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        return [int(x) for x in self.tokenizer.encode(text, add_special_tokens=add_special_tokens)]

    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        return self.tokenizer.decode([int(x) for x in token_ids], skip_special_tokens=skip_special_tokens)

    def token_surface(self, token_id: int) -> str:
        return self.decode([int(token_id)], skip_special_tokens=False)


def token_ids_to_structural_buckets(token_ids: Sequence[int], partition: VocabularyPartition) -> List[int]:
    buckets: List[int] = []
    for token_id in token_ids:
        token_id_i = int(token_id)
        bucket = int(partition.token_to_bucket[token_id_i]) if token_id_i < len(partition.token_to_bucket) else -1
        if bucket in (0, 1, 2):
            buckets.append(bucket)
        else:
            buckets.append(stable_hash_int(("fallback_payload_bit", token_id_i), modulo=2))
    return buckets


def payload_bits_from_buckets(token_ids: Sequence[int], buckets: Sequence[int]) -> List[int]:
    bits: List[int] = []
    for token_id, bucket in zip(token_ids, buckets):
        bucket_i = int(bucket)
        if bucket_i in (0, 1):
            bits.append(bucket_i)
        else:
            bits.append(stable_hash_int(("fallback_payload_bit", int(token_id)), modulo=2))
    return bits


def build_edited_token_bucket_ids_recovered(
    original_token_bucket_ids: Sequence[int],
    validated: Sequence[ValidatedInstruction],
) -> List[int]:
    inserts_after: Dict[int, List[int]] = {}
    subs_at: Dict[int, List[int]] = {}
    dels_at: set[int] = set()
    for item in validated:
        new_bucket_ids = [int(x) for x in item.structural_anchor.get("new_bucket_ids", [])]
        if item.op == "insert" and item.gap_after is not None:
            inserts_after.setdefault(int(item.gap_after), []).extend(new_bucket_ids)
        elif item.op == "substitute" and item.original_index is not None:
            subs_at[int(item.original_index)] = new_bucket_ids
        elif item.op == "delete" and item.original_index is not None:
            dels_at.add(int(item.original_index))

    edited: List[int] = []
    edited.extend(inserts_after.get(-1, []))
    for idx, bucket_id in enumerate(original_token_bucket_ids):
        if idx in dels_at:
            pass
        elif idx in subs_at:
            edited.extend(subs_at[idx])
        else:
            edited.append(int(bucket_id))
        edited.extend(inserts_after.get(idx, []))
    return edited


def structural_metadata_from_token_buckets(
    edited_token_ids: Sequence[int],
    edited_token_bucket_ids: Sequence[int],
) -> Tuple[List[int], List[int], List[int]]:
    symbols: List[int] = []
    indices: List[int] = []
    seq: List[int] = []
    cursor = 0
    for bucket in edited_token_bucket_ids:
        bucket_i = int(bucket)
        if bucket_i in (0, 1, 2):
            symbols.append(bucket_i)
            indices.append(cursor)
            seq.append(bucket_i)
            cursor += 1
        else:
            symbols.append(-1)
            indices.append(-1)
    if len(symbols) != len(edited_token_ids):
        raise RuntimeError("Edited token/bucket metadata length mismatch.")
    return symbols, indices, seq


def validate_with_boundary_edits(
    parsed_json: Dict[str, Any],
    units,
    text_token_ids: Sequence[int],
    original_payload_blocks: Sequence[Sequence[int]],
    partition: VocabularyPartition,
    model,
    max_edited_blocks: int,
    max_edit_instructions: int,
    max_block_edit_rate: float,
) -> Tuple[List[ValidatedInstruction], Optional[str]]:
    if not isinstance(parsed_json, dict):
        return [], "json_not_dict"
    edits = parsed_json.get("edits")
    if not isinstance(edits, list) or len(edits) == 0:
        return [], "missing_or_empty_edits"
    if len(edits) > int(max_edit_instructions):
        return [], "too_many_edit_instructions"
    if not units:
        return [], "no_text_units"

    block_len = len(original_payload_blocks[0]) if original_payload_blocks else 7
    num_blocks = len(original_payload_blocks)
    total_payload_bits = sum(len(block) for block in original_payload_blocks)
    index_to_unit = {unit.index: unit for unit in units}
    text_pos_anchors = set()
    text_gap_anchors = set()
    payload_pos_anchors = set()
    payload_gap_anchors = set()
    boundary_pos_anchors = set()
    validated: List[ValidatedInstruction] = []

    for raw_edit in edits:
        if not isinstance(raw_edit, dict):
            return [], "edit_not_dict"
        op = str(raw_edit.get("op", "")).strip().lower()
        if op not in {"substitute", "delete", "insert"}:
            return [], f"invalid_op:{op}"
        original_text = str(raw_edit.get("original_text", "") or "")
        reason = str(raw_edit.get("reason", "") or "")
        new_content = str(raw_edit.get("new_content", "") or "")
        if op in {"substitute", "insert"} and not str(new_content).strip():
            return [], f"{op}_missing_new_content"
        tokenized_new_ids = tokenize_new_content(model, new_content) if op in {"substitute", "insert"} else []
        new_bucket_ids = token_ids_to_structural_buckets(tokenized_new_ids, partition) if op in {"substitute", "insert"} else []
        mapped_new_bits = payload_bits_from_buckets(tokenized_new_ids, new_bucket_ids) if op in {"substitute", "insert"} else []

        if op in {"substitute", "delete"}:
            if "index" not in raw_edit:
                return [], "missing_index"
            idx = int(raw_edit["index"])
            if idx not in index_to_unit:
                return [], "index_out_of_range"
            if idx in text_pos_anchors:
                return [], "duplicate_text_index"
            unit = index_to_unit[idx]
            local_window = local_window_for_index(text_token_ids, model, idx)
            if not approx_text_match(original_text, unit.surface, local_window):
                return [], "original_text_mismatch"

            bucket_id = int(unit.approx_bucket_id)
            if bucket_id in (0, 1) and unit.is_payload_token:
                payload_pos = int(unit.payload_index)
                if payload_pos in payload_pos_anchors:
                    return [], "duplicate_payload_position"
                payload_pos_anchors.add(payload_pos)
                text_pos_anchors.add(idx)
                block_id, payload_offset = global_payload_pos_to_block_offset(payload_pos, block_len)
                if op == "substitute":
                    if not tokenized_new_ids or not mapped_new_bits:
                        return [], "substitute_missing_new_content"
                    original_bit = int(original_payload_blocks[block_id][payload_offset])
                    replacement_bits = [int(x) for x in mapped_new_bits]
                    block_events = {
                        block_id: [EditEvent("sub", ("payload", payload_offset), value_before=original_bit, value_after=replacement_bits[0])]
                    }
                    if len(replacement_bits) > 1:
                        block_events[block_id].extend(
                            EditEvent("insert", ("gap", min(block_len, payload_offset + 1)), value_after=int(bit))
                            for bit in replacement_bits[1:]
                        )
                    structural_anchor = {
                        "type": "payload_position",
                        "global_payload_index": payload_pos,
                        "block_id": block_id,
                        "payload_offset": payload_offset,
                        "new_bucket_ids": new_bucket_ids,
                    }
                else:
                    original_bit = int(original_payload_blocks[block_id][payload_offset])
                    block_events = {block_id: [EditEvent("delete", ("payload", payload_offset), value_before=original_bit)]}
                    structural_anchor = {
                        "type": "payload_position",
                        "global_payload_index": payload_pos,
                        "block_id": block_id,
                        "payload_offset": payload_offset,
                        "new_bucket_ids": [],
                    }
                affected_blocks = [block_id]
            elif bucket_id == 2:
                block_id = max(0, min(int(unit.block_id), max(0, num_blocks - 1)))
                boundary_key = (block_id, int(unit.index))
                if boundary_key in boundary_pos_anchors:
                    return [], "duplicate_boundary_position"
                boundary_pos_anchors.add(boundary_key)
                text_pos_anchors.add(idx)
                if op == "substitute":
                    if not tokenized_new_ids or not new_bucket_ids:
                        return [], "substitute_missing_new_content"
                    block_events = {
                        block_id: [EditEvent("sub", ("boundary", block_len), value_before=2, value_after=int(new_bucket_ids[0]))]
                    }
                    structural_anchor = {
                        "type": "boundary_position",
                        "block_id": block_id,
                        "boundary_offset": block_len,
                        "token_index": idx,
                        "new_bucket_ids": new_bucket_ids,
                    }
                else:
                    block_events = {block_id: [EditEvent("delete", ("boundary", block_len), value_before=2)]}
                    structural_anchor = {
                        "type": "boundary_position",
                        "block_id": block_id,
                        "boundary_offset": block_len,
                        "token_index": idx,
                        "new_bucket_ids": [],
                    }
                affected_blocks = [block_id]
            else:
                return [], "nonstructural_token_edit_unsupported"

            validated.append(
                ValidatedInstruction(
                    op=op,
                    original_index=idx,
                    gap_after=None,
                    original_text=original_text,
                    new_content=new_content,
                    reason=reason,
                    tokenized_new_ids=tokenized_new_ids,
                    mapped_new_bits=mapped_new_bits,
                    affected_blocks=affected_blocks,
                    block_events=block_events,
                    structural_anchor=structural_anchor,
                )
            )
        else:
            if "gap_after" not in raw_edit:
                return [], "missing_gap_after"
            gap_after = int(raw_edit["gap_after"])
            if gap_after < -1 or gap_after >= len(units):
                return [], "gap_after_out_of_range"
            if gap_after in text_gap_anchors:
                return [], "duplicate_text_gap"
            if not tokenized_new_ids or not mapped_new_bits:
                return [], "insert_missing_new_content"
            if gap_after < 0:
                gap_global = 0
            else:
                gap_global = int(index_to_unit[gap_after].payload_index) + 1
            gap_global = max(0, min(total_payload_bits, gap_global))
            block_id, gap_offset = global_gap_to_block_offset(gap_global, block_len, num_blocks)
            payload_gap_key = (block_id, gap_offset)
            if payload_gap_key in payload_gap_anchors:
                return [], "duplicate_payload_gap"
            payload_gap_anchors.add(payload_gap_key)
            text_gap_anchors.add(gap_after)
            block_events = {
                block_id: [EditEvent("insert", ("gap", gap_offset), value_after=int(bit)) for bit in mapped_new_bits]
            }
            validated.append(
                ValidatedInstruction(
                    op=op,
                    original_index=None,
                    gap_after=gap_after,
                    original_text=original_text,
                    new_content=new_content,
                    reason=reason,
                    tokenized_new_ids=tokenized_new_ids,
                    mapped_new_bits=mapped_new_bits,
                    affected_blocks=[block_id],
                    block_events=block_events,
                    structural_anchor={
                        "type": "payload_gap",
                        "global_gap_index": gap_global,
                        "block_id": block_id,
                        "gap_offset": gap_offset,
                        "new_bucket_ids": new_bucket_ids,
                    },
                )
            )

    all_affected_blocks = sorted({block for item in validated for block in item.affected_blocks})
    if not all_affected_blocks:
        return [], "no_affected_blocks"
    block_edit_rate = len(all_affected_blocks) / max(1, len(original_payload_blocks))
    if len(all_affected_blocks) > int(max_edited_blocks):
        return [], "too_many_edited_blocks"
    if block_edit_rate >= float(max_block_edit_rate):
        return [], "block_edit_rate_too_high"
    return validated, None


def gt_events_from_validated(num_blocks: int, validated: Sequence[ValidatedInstruction]) -> List[List[EditEvent]]:
    events: List[List[EditEvent]] = [[] for _ in range(num_blocks)]
    for item in validated:
        for block_id, block_events in item.block_events.items():
            if 0 <= int(block_id) < num_blocks:
                events[int(block_id)].extend(block_events)
    return events


def serialize_validated(validated: Sequence[ValidatedInstruction]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in validated:
        out.append(
            {
                "op": item.op,
                "original_index": item.original_index,
                "gap_after": item.gap_after,
                "original_text": item.original_text,
                "new_content": item.new_content,
                "reason": item.reason,
                "tokenized_new_ids": item.tokenized_new_ids,
                "mapped_new_bits": item.mapped_new_bits,
                "affected_blocks": item.affected_blocks,
                "block_events": {
                    str(block_id): [
                        {
                            "etype": ev.etype,
                            "loc": list(ev.loc),
                            "value_before": ev.value_before,
                            "value_after": ev.value_after,
                        }
                        for ev in events
                    ]
                    for block_id, events in item.block_events.items()
                },
                "structural_anchor": item.structural_anchor,
            }
        )
    return out


def recover_one(
    row: pd.Series,
    instruction_record: Dict[str, Any],
    source_by_sequence: Dict[int, pd.Series],
    model: TokenizerOnlyModel,
    partition: VocabularyPartition,
    codebook: EccCodebook,
    decoder_config: EccDecoderConfig,
    tolerance: int,
    max_edited_blocks: int,
    max_edit_instructions: int,
    max_block_edit_rate: float,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    sequence_index = int(row["sequence_index"])
    src = source_by_sequence[sequence_index]
    suffix_text = str(src["suffix_text"])
    parsed_output = instruction_record.get("parsed_output")
    if not isinstance(parsed_output, dict):
        raise RuntimeError("missing_parsed_output")

    saved_bucket_seq = parse_bucket_id_sequence(src["bucket_id_sequence"])
    original_payload_blocks = parse_payload_blocks_json(src["block_bucket_sequences_json"])
    saved_token_ids = parse_optional_int_list(src.get("generated_token_ids"))
    if not saved_token_ids:
        raise RuntimeError("missing_generated_token_ids")

    text_units, original_text_token_ids, original_token_block_map, original_token_bucket_ids = build_text_units_from_generated_tokens(
        model=model,
        token_ids=saved_token_ids,
        token_buckets=saved_bucket_seq,
        payload_blocks=original_payload_blocks,
    )
    original_block_text_spans = build_block_text_spans(
        original_text_token_ids,
        original_token_block_map,
        model,
        num_blocks=len(original_payload_blocks),
    )
    validated, error = validate_with_boundary_edits(
        parsed_json=parsed_output,
        units=text_units,
        text_token_ids=original_text_token_ids,
        original_payload_blocks=original_payload_blocks,
        partition=partition,
        model=model,
        max_edited_blocks=max_edited_blocks,
        max_edit_instructions=max_edit_instructions,
        max_block_edit_rate=max_block_edit_rate,
    )
    if error is not None:
        raise RuntimeError(error)

    edited_text_token_ids = []
    # Reuse the exact text-edit semantics: substitutions replace a token with
    # tokenized new_content, inserts add tokens after gap_after, deletes remove.
    from run_llm_editor_experiment import apply_validated_text_edits

    edited_text_token_ids = apply_validated_text_edits(original_text_token_ids, validated)
    edited_token_block_map = build_edited_token_block_map(
        original_text_token_ids=original_text_token_ids,
        original_token_block_map=original_token_block_map,
        validated=validated,
    )
    edited_token_bucket_ids = build_edited_token_bucket_ids_recovered(original_token_bucket_ids, validated)
    edited_token_structural_symbols, edited_token_structural_indices, observed_sequence = structural_metadata_from_token_buckets(
        edited_token_ids=edited_text_token_ids,
        edited_token_bucket_ids=edited_token_bucket_ids,
    )
    gt_events_per_block = gt_events_from_validated(len(original_payload_blocks), validated)
    pred_blocks = detect_sequence_multiple(
        observed_sequence,
        decoder_config=decoder_config,
        codebook=codebook,
    )
    ev = evaluate_predictions_multiple(
        original_payload_blocks=original_payload_blocks,
        gt_events_per_block=gt_events_per_block,
        pred_blocks=pred_blocks,
        tolerance=tolerance,
        codebook=codebook,
    )
    detector_block_details = build_detector_block_details(
        pred_blocks=pred_blocks,
        observed_sequence=observed_sequence,
        tolerance=tolerance,
        codebook=codebook,
        boundary_symbol=codebook.boundary_symbol,
    )
    detector_aligned_block_text_spans, edited_token_block_map_from_detector = build_detector_aligned_block_text_spans(
        edited_token_ids=edited_text_token_ids,
        edited_token_structural_indices=edited_token_structural_indices,
        detector_block_details=detector_block_details,
        model=model,
    )
    edited_block_text_spans = build_block_text_spans(
        edited_text_token_ids,
        edited_token_block_map,
        model,
        num_blocks=len(original_payload_blocks),
    )
    gt_blocks_flags = [int(len(events) > 0) for events in gt_events_per_block]
    pred_blocks_flags = [int(parsed_block_exceeds_tolerance(pb, tolerance=tolerance, codebook=codebook)) for pb in pred_blocks]
    edited_text = model.decode(edited_text_token_ids, skip_special_tokens=True)
    detail = row.to_dict()
    detail.update(
        {
            "used": True,
            "skip_reason": None,
            "recovery_status": "recovered_boundary_edit",
            "recovered_from_skip_reason": row.get("skip_reason"),
            "num_edited_blocks": int(sum(gt_blocks_flags)),
            "block_edit_rate": float(sum(gt_blocks_flags) / max(1, len(gt_blocks_flags))),
            "accepted_edit_json": json.dumps(parsed_output, ensure_ascii=False),
            "gt_blocks": json.dumps(gt_blocks_flags),
            "pred_blocks": json.dumps(pred_blocks_flags),
            "TP": int(ev["TP"]),
            "FP": int(ev["FP"]),
            "FN": int(ev["FN"]),
            "TN": int(ev["TN"]),
            "block_tpr": float(ev["block_tpr"]),
            "block_far": float(ev["block_far"]),
            "candidate_coverage": float(ev["event_coverage_overall"]),
            "event_loc_hit": int(ev["event_loc_hit"]),
            "event_total_overall": int(ev["event_total_overall"]),
            "original_text": suffix_text,
            "edited_text": edited_text,
            "original_token_ids_json": json.dumps(list(original_text_token_ids)),
            "edited_token_ids_json": json.dumps(list(edited_text_token_ids)),
            "original_token_block_map_json": json.dumps(list(original_token_block_map)),
            "edited_token_block_map_json": json.dumps(list(edited_token_block_map)),
            "edited_token_bucket_ids_json": json.dumps(list(edited_token_bucket_ids)),
            "edited_token_structural_symbols_json": json.dumps(list(edited_token_structural_symbols)),
            "edited_token_structural_index_json": json.dumps(list(edited_token_structural_indices)),
            "edited_token_block_map_from_detector_json": json.dumps(list(edited_token_block_map_from_detector)),
            "edited_structural_sequence_json": json.dumps(list(observed_sequence)),
            "pred_blocks_detailed_json": json.dumps(detector_block_details, ensure_ascii=False),
            "detector_aligned_block_text_spans_json": json.dumps(detector_aligned_block_text_spans, ensure_ascii=False),
            "original_block_text_spans_json": json.dumps(original_block_text_spans, ensure_ascii=False),
            "edited_block_text_spans_json": json.dumps(edited_block_text_spans, ensure_ascii=False),
        }
    )
    instruction = dict(instruction_record)
    instruction.update(
        {
            "used": True,
            "skip_reason": None,
            "accepted_edit_json": parsed_output,
            "validated_instructions": serialize_validated(validated),
            "recovery_status": "recovered_boundary_edit",
            "recovered_from_skip_reason": row.get("skip_reason"),
            "edited_token_block_map": list(edited_token_block_map),
            "edited_token_bucket_ids": list(edited_token_bucket_ids),
            "edited_token_structural_symbols": list(edited_token_structural_symbols),
            "edited_token_structural_indices": list(edited_token_structural_indices),
            "edited_token_block_map_from_detector": list(edited_token_block_map_from_detector),
            "edited_structural_sequence": list(observed_sequence),
            "pred_blocks_detailed": detector_block_details,
            "detector_aligned_block_text_spans": detector_aligned_block_text_spans,
            "edited_block_text_spans": edited_block_text_spans,
        }
    )
    return detail, instruction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover LLM editor rows skipped only because edits targeted ECC boundary tokens.")
    parser.add_argument("--source-csv", required=True)
    parser.add_argument("--editor-output-dir", required=True)
    parser.add_argument("--partition-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name", default="Qwen/Qwen3-8B")
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--tolerance", type=int, default=1)
    parser.add_argument("--decoder-max-edits-per-block", type=int, default=3)
    parser.add_argument("--max-edited-blocks", type=int, default=12)
    parser.add_argument("--max-edit-instructions", type=int, default=10)
    parser.add_argument("--max-block-edit-rate", type=float, default=1.01)
    parser.add_argument("--recover-skip-reason", default="nonpayload_token_edit_unsupported")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_dir(args.output_dir)
    editor_dir = Path(args.editor_output_dir)
    source_df = load_seed_dataframe(args.source_csv, num_samples=None)
    source_by_sequence = {int(row["sequence_index"]): row for _, row in source_df.iterrows()}
    details_df = pd.read_csv(editor_dir / "llm_editor_details.csv")
    instruction_records = json.loads((editor_dir / "llm_edit_instructions.json").read_text(encoding="utf-8"))
    instruction_by_key = {
        (int(rec["sequence_index"]), str(rec["motivation"]), str(rec["intent_label"])): rec
        for rec in instruction_records
    }

    model = TokenizerOnlyModel(args.model_name)
    partition = load_vocabulary_partition(args.partition_dir)
    if len(partition.token_to_bucket) != model.vocab_size:
        raise RuntimeError(f"Partition/tokenizer vocab mismatch: {len(partition.token_to_bucket)} vs {model.vocab_size}")
    codebook = EccCodebook(block_len=args.block_len, vt_a=args.vt_a)
    decoder_config = EccDecoderConfig(
        decoder_max_edits_per_block=args.decoder_max_edits_per_block,
        boundary_edit_modes=("delete", "sub"),
    )

    recovered_count = 0
    failed_count = 0
    rows: List[Dict[str, Any]] = []
    new_instruction_records: List[Dict[str, Any]] = []
    failure_rows: List[Dict[str, Any]] = []
    for _, row in details_df.iterrows():
        row_dict = row.to_dict()
        if pd.isna(row_dict.get("recovery_status", math.nan)):
            row_dict["recovery_status"] = "original_used" if bool(row_dict.get("used")) else "original_skipped"
        key = (int(row["sequence_index"]), str(row["motivation"]), str(row["intent_label"]))
        rec = instruction_by_key.get(key)
        if str(row.get("skip_reason")) == args.recover_skip_reason and rec is not None:
            try:
                recovered_row, recovered_record = recover_one(
                    row=row,
                    instruction_record=rec,
                    source_by_sequence=source_by_sequence,
                    model=model,
                    partition=partition,
                    codebook=codebook,
                    decoder_config=decoder_config,
                    tolerance=args.tolerance,
                    max_edited_blocks=args.max_edited_blocks,
                    max_edit_instructions=args.max_edit_instructions,
                    max_block_edit_rate=args.max_block_edit_rate,
                )
                rows.append(recovered_row)
                new_instruction_records.append(recovered_record)
                recovered_count += 1
                continue
            except Exception as exc:
                row_dict["recovery_status"] = "recovery_failed"
                row_dict["recovery_failure_reason"] = str(exc)
                failure_rows.append(
                    {
                        "sequence_index": int(row["sequence_index"]),
                        "motivation": str(row["motivation"]),
                        "intent_label": str(row["intent_label"]),
                        "failure_reason": str(exc),
                    }
                )
                failed_count += 1
        rows.append(row_dict)
        if rec is not None:
            rec_out = dict(rec)
            rec_out.setdefault("recovery_status", row_dict.get("recovery_status"))
            new_instruction_records.append(rec_out)

    detail_df = pd.DataFrame(rows)
    summary_df = build_summary_dataframe(detail_df.to_dict(orient="records"))
    output_dir = Path(args.output_dir)
    save_dataframe(summary_df, str(output_dir / "llm_editor_summary"), save_parquet=True)
    save_dataframe(detail_df, str(output_dir / "llm_editor_details"), save_parquet=True)
    write_json(str(output_dir / "llm_edit_instructions.json"), new_instruction_records)
    write_json(
        str(output_dir / "boundary_recovery_report.json"),
        {
            "source_csv": args.source_csv,
            "editor_output_dir": args.editor_output_dir,
            "partition_dir": args.partition_dir,
            "recover_skip_reason": args.recover_skip_reason,
            "input_rows": int(len(details_df)),
            "input_used": int((details_df["used"] == True).sum()),  # noqa: E712
            "recovered_count": int(recovered_count),
            "failed_count": int(failed_count),
            "output_used": int((detail_df["used"] == True).sum()),  # noqa: E712
            "failures": failure_rows[:100],
            "note": "Boundary-token substitute/delete edits are replayed from saved LLM JSON without re-calling the editor model.",
        },
    )
    print(f"Recovered {recovered_count} rows; failed {failed_count}.")
    print(f"Wrote {output_dir / 'llm_editor_details.csv'}")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
