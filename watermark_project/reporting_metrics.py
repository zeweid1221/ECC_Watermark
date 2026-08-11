from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence


def coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n", "", "nan", "none"}:
            return False
    if value is None:
        return False
    try:
        if math.isnan(value):
            return False
    except (TypeError, ValueError):
        pass
    return bool(value)


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return math.nan
    return float(numerator) / float(denominator)


def document_alarm_metrics(
    confusion_rows: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    rows = list(confusion_rows)
    if not rows:
        return {
            "mean_false_blocks_per_document": math.nan,
            "documents_with_false_alarm": 0,
            "document_false_alarm_rate": math.nan,
            "block_precision": math.nan,
        }

    fp_values = [int(row.get("FP", 0)) for row in rows]
    tp = sum(int(row.get("TP", 0)) for row in rows)
    fp = sum(fp_values)
    documents_with_false_alarm = sum(value > 0 for value in fp_values)
    return {
        "mean_false_blocks_per_document": float(sum(fp_values)) / len(rows),
        "documents_with_false_alarm": int(documents_with_false_alarm),
        "document_false_alarm_rate": float(documents_with_false_alarm) / len(rows),
        "block_precision": safe_ratio(tp, tp + fp),
    }


def editor_structural_visibility_metrics(
    *,
    original_token_ids: Sequence[int],
    original_token_block_map: Sequence[int],
    edited_structural_symbols: Sequence[int],
    edited_token_provenance: Sequence[Mapping[str, Any]],
    gt_block_flags: Sequence[int],
    pred_block_flags: Sequence[int],
    token_to_bucket: Sequence[int],
    accepted_edit_json: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    if len(original_token_ids) != len(original_token_block_map):
        raise ValueError("Original token ids and block map must have equal lengths.")
    if len(edited_structural_symbols) != len(edited_token_provenance):
        raise ValueError("Edited structural symbols and provenance must have equal lengths.")

    num_blocks = len(gt_block_flags)
    original_by_block: Dict[int, List[int]] = defaultdict(list)
    for token_id, block_id in zip(original_token_ids, original_token_block_map):
        block_id = int(block_id)
        if 0 <= block_id < num_blocks:
            token_id = int(token_id)
            if not 0 <= token_id < len(token_to_bucket):
                raise ValueError(f"Original token id {token_id} is outside the partition.")
            original_by_block[block_id].append(int(token_to_bucket[token_id]))

    edited_by_block: Dict[int, List[int]] = defaultdict(list)
    unassigned_edited_symbols = 0
    substitute_symbols: Dict[int, List[tuple[int, int]]] = defaultdict(list)
    for symbol, provenance in zip(edited_structural_symbols, edited_token_provenance):
        block_id = provenance.get("original_block_id")
        if block_id is None or not 0 <= int(block_id) < num_blocks:
            unassigned_edited_symbols += 1
        else:
            edited_by_block[int(block_id)].append(int(symbol))
        if provenance.get("origin") == "substitute" and provenance.get("original_token_index") is not None:
            substitute_symbols[int(provenance["original_token_index"])].append(
                (int(provenance.get("replacement_offset", 0)), int(symbol))
            )

    visible_flags: List[int] = []
    invisible_flags: List[int] = []
    for block_id, gt_flag in enumerate(gt_block_flags):
        edited = bool(int(gt_flag))
        structurally_changed = original_by_block[block_id] != edited_by_block[block_id]
        visible_flags.append(int(edited and structurally_changed))
        invisible_flags.append(int(edited and not structurally_changed))

    visible_blocks = sum(visible_flags)
    invisible_blocks = sum(invisible_flags)
    visible_flagged = sum(
        int(visible_flags[index] and index < len(pred_block_flags) and int(pred_block_flags[index]))
        for index in range(num_blocks)
    )
    invisible_flagged = sum(
        int(invisible_flags[index] and index < len(pred_block_flags) and int(pred_block_flags[index]))
        for index in range(num_blocks)
    )

    substitution_counts = {
        "num_substitute_instructions": 0,
        "num_single_token_same_bucket_substitutions": 0,
        "num_single_token_cross_bucket_substitutions": 0,
        "num_multi_token_substitutions": 0,
        "num_unclassified_substitutions": 0,
    }
    edits = accepted_edit_json.get("edits", []) if accepted_edit_json else []
    for edit in edits:
        if not isinstance(edit, Mapping) or str(edit.get("op", "")).lower() != "substitute":
            continue
        substitution_counts["num_substitute_instructions"] += 1
        if edit.get("index") is None:
            substitution_counts["num_unclassified_substitutions"] += 1
            continue
        original_index = int(edit["index"])
        if not 0 <= original_index < len(original_token_ids):
            substitution_counts["num_unclassified_substitutions"] += 1
            continue
        replacements = [
            symbol for _, symbol in sorted(substitute_symbols.get(original_index, []))
        ]
        original_token_id = int(original_token_ids[original_index])
        if not replacements or not 0 <= original_token_id < len(token_to_bucket):
            substitution_counts["num_unclassified_substitutions"] += 1
            continue
        original_symbol = int(token_to_bucket[original_token_id])
        if len(replacements) > 1:
            substitution_counts["num_multi_token_substitutions"] += 1
        elif replacements[0] == original_symbol:
            substitution_counts["num_single_token_same_bucket_substitutions"] += 1
        else:
            substitution_counts["num_single_token_cross_bucket_substitutions"] += 1

    return {
        **substitution_counts,
        "num_structurally_visible_edited_blocks": int(visible_blocks),
        "num_structurally_invisible_edited_blocks": int(invisible_blocks),
        "num_visible_edited_blocks_flagged": int(visible_flagged),
        "num_invisible_edited_blocks_flagged": int(invisible_flagged),
        "structural_visibility_rate": safe_ratio(
            visible_blocks, visible_blocks + invisible_blocks
        ),
        "visible_block_tpr": safe_ratio(visible_flagged, visible_blocks),
        "invisible_block_alarm_rate": safe_ratio(invisible_flagged, invisible_blocks),
        "num_unassigned_edited_symbols": int(unassigned_edited_symbols),
        "structurally_visible_gt_blocks_json": visible_flags,
        "structurally_invisible_gt_blocks_json": invisible_flags,
    }
