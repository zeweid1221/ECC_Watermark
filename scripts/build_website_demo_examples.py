from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "outputs" / "paper_results_current"
MANIFEST = json.loads(
    (ARCHIVE / "ARCHIVE_MANIFEST.json").read_text(encoding="utf-8")
)
DEMO_FILES = MANIFEST["components"]["website_demo_examples"]
EDITOR_FILES = {
    5: ARCHIVE / DEMO_FILES["editor_delta5"],
    20: ARCHIVE / DEMO_FILES["editor_delta20"],
}
SOURCE = ARCHIVE / DEMO_FILES["source_details"]
OUTPUT = ROOT / "website" / "src" / "demoExamples.js"
TOKENIZER_NAME = "Qwen/Qwen3-8B"


def parse_json(value: str, default: Any) -> Any:
    if value is None or value == "":
        return default
    return json.loads(value)


def row_score(row: Dict[str, str]) -> float:
    return (
        float(row["block_tpr"])
        - float(row["block_far"])
        + 0.2 * float(row["candidate_coverage"])
    )


def instruction_realization_rate(row: Dict[str, str]) -> float:
    edits = parse_json(row["accepted_edit_json"], {"edits": []}).get("edits", [])
    if not edits:
        return 0.0
    source = str(row["original_text"])
    edited = str(row["edited_text"])
    realized = 0
    for edit in edits:
        op = str(edit.get("op", "")).lower()
        original = str(edit.get("original_text", ""))
        replacement = str(edit.get("new_content", ""))
        if op == "substitute":
            matched = (
                source.count(original) > edited.count(original)
                and edited.count(replacement) > source.count(replacement)
            )
        elif op == "insert":
            matched = edited.count(replacement) > source.count(replacement)
        else:
            matched = source.count(original) > edited.count(original)
        realized += int(matched)
    return realized / len(edits)


def choose_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_motivation: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_motivation[row["motivation"]].append(row)

    selected: List[Dict[str, str]] = []
    for motivation in sorted(by_motivation):
        all_candidates = by_motivation[motivation]
        candidates = [
            row for row in all_candidates if instruction_realization_rate(row) >= 0.6
        ]
        delta5 = sorted(
            (row for row in candidates if int(float(row["logit_bias"])) == 5),
            key=lambda row: (-row_score(row), int(row["sequence_index"])),
        )
        delta20 = sorted(
            (row for row in candidates if int(float(row["logit_bias"])) == 20),
            key=lambda row: (-row_score(row), int(row["sequence_index"])),
        )
        selected.extend(delta5[:1] + delta20[:2])
    return selected


def bucket_description(bucket_ids: List[int]) -> str:
    labels = []
    for bucket_id in sorted(set(bucket_ids)):
        labels.append("boundary anchor" if bucket_id == 2 else f"payload bit {bucket_id}")
    return ", ".join(labels) if labels else "deleted source position"


def build_token_offsets(tokenizer: Any, text: str, token_ids: List[int]) -> List[List[int]]:
    decoded = tokenizer.decode(
        token_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    if decoded != text:
        raise RuntimeError("Saved edited token ids do not decode to edited_text")

    # Decode prefixes because decoded text is not guaranteed to re-tokenize to the
    # same BPE sequence. Prefix lengths still recover the exact displayed spans.
    boundaries = [0]
    for end in range(1, len(token_ids) + 1):
        prefix = tokenizer.decode(
            token_ids[:end],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        boundaries.append(len(prefix))
    if boundaries != sorted(boundaries) or boundaries[-1] != len(text):
        raise RuntimeError("Could not recover monotonic token offsets from edited token ids")
    return [[boundaries[index], boundaries[index + 1]] for index in range(len(token_ids))]


def build_example(
    row: Dict[str, str],
    source_generated: Dict[int, List[Dict[str, Any]]],
    tokenizer: Any,
) -> Dict[str, Any]:
    bias = int(float(row["logit_bias"]))
    sequence_index = int(row["sequence_index"])
    source = source_generated[bias][sequence_index]

    accepted = parse_json(row["accepted_edit_json"], {"edits": []})
    gt_flags = [int(x) for x in parse_json(row["gt_blocks"], [])]
    pred_flags = [int(x) for x in parse_json(row["pred_blocks"], [])]
    original_block_map = [int(x) for x in parse_json(row["original_token_block_map_json"], [])]
    source_buckets = [int(x) for x in source.get("generated_bucket_seq", [])]
    provenance = parse_json(row["edited_token_provenance_json"], [])
    edited_token_ids = [int(x) for x in parse_json(row["edited_token_ids_json"], [])]
    edited_text = str(row["edited_text"])
    token_offsets = build_token_offsets(tokenizer, edited_text, edited_token_ids)
    parsed_details = parse_json(row["pred_blocks_detailed_json"], [])
    parsed_to_source = parse_json(row["parsed_to_source_blocks_json"], [])
    aligned_spans = parse_json(row["detector_aligned_block_text_spans_json"], {})
    source_candidates = parse_json(row.get("source_candidate_locations_json", ""), [])
    flagged_candidate_sizes = [
        len(source_candidates[index])
        for index, value in enumerate(pred_flags)
        if value and index < len(source_candidates)
    ]
    mean_candidate_size = (
        sum(flagged_candidate_sizes) / len(flagged_candidate_sizes)
        if flagged_candidate_sizes
        else 0.0
    )

    parsed_by_source: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for detail in parsed_details:
        parsed_index = int(detail.get("parsed_block_index", 0))
        source_ids = parsed_to_source[parsed_index] if parsed_index < len(parsed_to_source) else [parsed_index]
        for source_id in source_ids:
            parsed_by_source[int(source_id)].append(detail)

    edits = []
    for edit in accepted.get("edits", []):
        op = str(edit.get("op", "")).lower()
        anchor = int(edit.get("index", edit.get("gap_after", 0)))
        block_anchor = min(anchor, max(0, len(original_block_map) - 1))
        anchor_block = original_block_map[block_anchor] if original_block_map else anchor // 8

        if op == "insert":
            matching_provenance = [
                (edited_index, item)
                for edited_index, item in enumerate(provenance)
                if item.get("origin") == "insert" and int(item.get("gap_after", -2)) == anchor
            ]
        elif op == "substitute":
            matching_provenance = [
                (edited_index, item)
                for edited_index, item in enumerate(provenance)
                if item.get("origin") == "substitute"
                and int(item.get("original_token_index", -2)) == anchor
            ]
        else:
            matching_provenance = []

        bucket_ids = [
            int(item["edited_structural_symbol"])
            for _, item in matching_provenance
            if item.get("edited_structural_symbol") is not None
        ]
        structural_indices = [
            int(item["edited_structural_index"])
            for _, item in matching_provenance
            if item.get("edited_structural_index") is not None
        ]
        edited_positions = [edited_index for edited_index, _ in matching_provenance]
        highlight_start = (
            min(token_offsets[index][0] for index in edited_positions)
            if edited_positions
            else None
        )
        highlight_end = (
            max(token_offsets[index][1] for index in edited_positions)
            if edited_positions
            else None
        )
        if not bucket_ids and anchor < len(source_buckets):
            bucket_ids = [source_buckets[anchor]]
        if not structural_indices:
            structural_indices = [anchor]

        detector_options = parsed_by_source.get(anchor_block, [])
        detector_detail = next(
            (item for item in detector_options if bool(item.get("exceeds_tolerance"))),
            detector_options[0] if detector_options else {},
        )
        parsed_index = int(detector_detail.get("parsed_block_index", anchor_block))

        edits.append(
            {
                "op": op,
                "anchor": anchor,
                "originalText": str(edit.get("original_text", "")),
                "newContent": str(edit.get("new_content", "")),
                "reason": str(edit.get("reason", "")),
                "highlightStart": highlight_start,
                "highlightEnd": highlight_end,
                "anchorToken": {
                    "tokenIndex": anchor,
                    "surface": str(edit.get("original_text", "")) or "insertion gap",
                    "bucketId": bucket_ids[0] if bucket_ids else None,
                    "structuralIndex": structural_indices[0] if structural_indices else anchor,
                    "blockId": anchor_block,
                    "isEditAnchor": True,
                },
                "bucketIds": bucket_ids,
                "structuralIndices": structural_indices,
                "bucketMeaning": bucket_description(bucket_ids),
                "anchorBlock": anchor_block,
                "detectorBlock": parsed_index,
                "detectorSnippet": str(aligned_spans.get(str(parsed_index), "")),
                "payloadDistance": detector_detail.get("payload_distance"),
                "observedSegment": detector_detail.get("observed_structural_segment", []),
                "decodedCodeword": detector_detail.get("decoded_codeword") or [],
                "candidateLocations": detector_detail.get("candidate_edit_locations", []),
            }
        )

    flagged_blocks = []
    for detail in parsed_details:
        if not bool(detail.get("exceeds_tolerance")):
            continue
        parsed_index = int(detail.get("parsed_block_index", 0))
        source_ids = parsed_to_source[parsed_index] if parsed_index < len(parsed_to_source) else [parsed_index]
        block_id = int(source_ids[0]) if source_ids else parsed_index
        flagged_blocks.append(
            {
                "blockId": block_id,
                "parsedBlockIndex": parsed_index,
                "snippet": str(aligned_spans.get(str(parsed_index), "")),
                "observedSegment": detail.get("observed_structural_segment", []),
                "decodedCodeword": detail.get("decoded_codeword") or [],
                "candidateLocations": detail.get("candidate_edit_locations", []),
                "payloadDistance": detail.get("payload_distance"),
                "boundaryState": detail.get("boundary_state"),
                "isGroundTruthEdited": any(
                    0 <= int(source_id) < len(gt_flags) and gt_flags[int(source_id)] == 1
                    for source_id in source_ids
                ),
            }
        )

    return {
        "id": f"delta-{bias}-seq-{sequence_index}",
        "sequenceIndex": sequence_index,
        "logitBias": bias,
        "numBlocks": len(gt_flags),
        "title": f"{row['motivation'].replace('_', ' ')} ({row['intent_label']}, delta={bias})",
        "motivation": row["motivation"],
        "intentLabel": row["intent_label"],
        "question": str(source.get("prompt", "")),
        "sourceAnswer": row["original_text"],
        "editedAnswer": edited_text,
        "edits": edits,
        "gtBlocks": [index for index, value in enumerate(gt_flags) if value],
        "predictedBlocks": [index for index, value in enumerate(pred_flags) if value],
        "metrics": {
            "blockTpr": float(row["block_tpr"]),
            "blockFar": float(row["block_far"]),
            "candidateCoverage": float(row["candidate_coverage"]),
            "meanCandidateSize": mean_candidate_size,
        },
        "flaggedBlocks": flagged_blocks,
    }


def main() -> None:
    rows = []
    for bias, editor_file in EDITOR_FILES.items():
        with editor_file.open("r", encoding="utf-8-sig", newline="") as handle:
            bias_rows = list(csv.DictReader(handle))
        for row in bias_rows:
            row["logit_bias"] = str(bias)
        rows.extend(bias_rows)
    source_payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_generated = {
        int(float(setting["logit_bias"])): setting["generated"]
        for setting in source_payload["settings"]
    }

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, local_files_only=True)
    selected = choose_rows(rows)
    examples = [build_example(row, source_generated, tokenizer) for row in selected]
    if len(examples) != 18:
        raise RuntimeError(f"Expected 18 demo examples, found {len(examples)}")
    if any(not example["flaggedBlocks"] for example in examples):
        raise RuntimeError("Every selected demo example must include at least one detector alarm")

    rendered = "export const demoExamples = " + json.dumps(
        examples, ensure_ascii=False, indent=2
    ) + ";\n"
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {len(examples)} examples to {OUTPUT}")


if __name__ == "__main__":
    main()
