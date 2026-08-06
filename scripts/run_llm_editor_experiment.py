from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

try:
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
except Exception:  # pragma: no cover
    torch = None
    AutoModelForCausalLM = None
    BitsAndBytesConfig = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from watermark_project.config import ECCConfig, ModelConfig
from watermark_project.ecc_detector import (
    EccCodebook,
    EccDecoderConfig,
    detect_sequence_multiple,
    evaluate_predictions_with_provenance,
    parsed_block_exceeds_tolerance,
)
from watermark_project.edits import EditEvent
from watermark_project.io_utils import ensure_dir, save_dataframe, to_jsonable, write_json
from watermark_project.modeling import HfLanguageModel, build_language_model, clean_text, stable_hash_int
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile
from watermark_project.partitioning import (
    VocabularyPartition,
    build_vocabulary_partition,
    load_vocabulary_partition,
    save_vocabulary_partition,
    validate_vocabulary_partition,
)


BENIGN_MOTIVATIONS = {"grammar_polish", "clarity_improvement", "style_softening"}
MALICIOUS_MOTIVATIONS = {"claim_distortion", "stance_shift", "source_spoofing"}
ALL_MOTIVATIONS = BENIGN_MOTIVATIONS | MALICIOUS_MOTIVATIONS


class EditorSingleGpu4BitHfLanguageModel(HfLanguageModel):
    """Local editor loader for fitting Qwen-sized models on one small CUDA GPU."""

    def _load_model(self, config: ModelConfig, model_kwargs: Dict[str, object], compute_dtype) -> object:
        if config.use_4bit and self.device.startswith("cuda"):
            if AutoModelForCausalLM is None or BitsAndBytesConfig is None or torch is None:
                raise RuntimeError("transformers/torch 4-bit support is unavailable in this environment.")
            quant_kwargs = dict(model_kwargs)
            quant_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
            quant_kwargs["device_map"] = {"": 0}
            quant_kwargs["max_memory"] = {0: "7GiB", "cpu": "6GiB"}
            quant_kwargs["offload_state_dict"] = True
            quant_kwargs["local_files_only"] = bool(os.environ.get("HF_HUB_OFFLINE") or os.environ.get("TRANSFORMERS_OFFLINE"))
            quant_kwargs.pop("torch_dtype", None)
            quant_kwargs["dtype"] = torch.float16
            model = AutoModelForCausalLM.from_pretrained(config.model_name, **quant_kwargs)
            self._quantization_mode = "4bit"
            print(f"[info] Loaded {config.model_name} with single-GPU 4-bit quantization on {self.device}.")
            return model
        return super()._load_model(config, model_kwargs, compute_dtype)


@dataclass
class TextUnit:
    index: int
    token_id: int
    surface: str
    block_id: int
    payload_index: int
    payload_offset: int
    approx_bucket_id: int
    structural_index: Optional[int] = None
    is_payload_token: bool = True


@dataclass
class ValidatedInstruction:
    op: str
    original_index: Optional[int]
    gap_after: Optional[int]
    original_text: str
    new_content: str
    reason: str
    tokenized_new_ids: List[int]
    mapped_new_buckets: List[int]
    affected_blocks: List[int]
    block_events: Dict[int, List[EditEvent]]
    structural_anchor: Dict[str, Any]


def parse_csv_strs(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def canonical_intent_label(motivation: str) -> str:
    if motivation in BENIGN_MOTIVATIONS:
        return "benign"
    if motivation in MALICIOUS_MOTIVATIONS:
        return "malicious"
    raise ValueError(f"Unknown motivation: {motivation}")


def parse_bucket_id_sequence(value: str) -> List[int]:
    raw = str(value).strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [int(x) for x in parsed]
    except Exception:
        pass
    return [int(x) for x in raw.split() if str(x).strip()]


def parse_payload_blocks_json(value: str) -> List[List[int]]:
    raw = json.loads(value)
    return [[int(x) for x in block] for block in raw]


def parse_optional_int_list(value: Any) -> List[int]:
    if value is None:
        return []
    try:
        if pd.isna(value):
            return []
    except Exception:
        pass
    raw = str(value).strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [int(x) for x in parsed if x is not None]
    except Exception:
        pass
    return [int(x) for x in raw.split() if str(x).strip()]


def flatten_payload_blocks_with_boundaries(payload_blocks: Sequence[Sequence[int]], boundary_symbol: int = 2) -> List[int]:
    seq: List[int] = []
    for block in payload_blocks:
        seq.extend(int(x) for x in block)
        seq.append(boundary_symbol)
    return seq


def payload_index_mapping(num_text_tokens: int, total_payload_bits: int) -> List[int]:
    if total_payload_bits <= 0:
        return []
    if num_text_tokens <= 0:
        return []
    mapping: List[int] = []
    for idx in range(num_text_tokens):
        mapped = int((idx * total_payload_bits) / max(1, num_text_tokens))
        mapping.append(min(total_payload_bits - 1, mapped))
    return mapping


def global_payload_pos_to_block_offset(global_pos: int, block_len: int) -> Tuple[int, int]:
    return int(global_pos) // int(block_len), int(global_pos) % int(block_len)


def global_gap_to_block_offset(gap_global: int, block_len: int, num_blocks: int) -> Tuple[int, int]:
    gap_global = int(gap_global)
    if gap_global <= 0:
        return 0, 0
    total_payload = block_len * num_blocks
    if gap_global >= total_payload:
        return num_blocks - 1, block_len
    if gap_global % block_len == 0:
        return max(0, gap_global // block_len - 1), block_len
    return gap_global // block_len, gap_global % block_len


def approx_text_match(expected: str, actual_surface: str, local_window: str) -> bool:
    expected_norm = normalize_text_match(expected)
    if not expected_norm:
        return True
    actual_norm = normalize_text_match(actual_surface)
    local_norm = normalize_text_match(local_window)
    return expected_norm in actual_norm or expected_norm in local_norm


def normalize_text_match(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(text).lower())).strip()


def extract_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    stripped = raw_text.strip()
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(stripped[start : end + 1])
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
    return None


def load_seed_dataframe(csv_path: str, num_samples: Optional[int]) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = normalize_seed_dataframe(df)
    if num_samples is not None:
        df = df.head(int(num_samples)).copy()
    return df.reset_index(drop=True)


def normalize_seed_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Accept both the original editor seed schema and preview_generation CSVs."""
    required = {"sequence_index", "prompt", "suffix_text", "bucket_id_sequence", "block_bucket_sequences_json"}
    if required.issubset(df.columns):
        return df

    preview_required = {"sample_index", "raw_prompt", "watermarked_text", "generated_bucket_seq", "block_summaries"}
    if not preview_required.issubset(df.columns):
        return df

    out = df.copy()
    out["sequence_index"] = out["sample_index"].astype(int)
    out["prompt"] = out["raw_prompt"].astype(str)
    out["suffix_text"] = out["watermarked_text"].astype(str)
    out["bucket_id_sequence"] = out["generated_bucket_seq"].astype(str)

    def _blocks_from_summaries(value: str) -> str:
        summaries = json.loads(str(value))
        blocks = []
        for summary in summaries:
            if isinstance(summary, dict) and "bits_prefix_capped" in summary:
                blocks.append([int(x) for x in summary["bits_prefix_capped"]])
        return json.dumps(blocks)

    out["block_bucket_sequences_json"] = out["block_summaries"].apply(_blocks_from_summaries)
    return out


def build_partition_texts(seed_df: pd.DataFrame) -> List[str]:
    prompts = [clean_text(x) for x in seed_df["prompt"].dropna().tolist()]
    seen = set()
    out = []
    for prompt in prompts:
        if prompt and prompt not in seen:
            out.append(prompt)
            seen.add(prompt)
    return out


def load_partition_texts(args: argparse.Namespace, seed_df: pd.DataFrame) -> Tuple[List[str], str, Optional[str]]:
    if args.partition_prompt_file:
        with open(args.partition_prompt_file, "r", encoding="utf-8") as handle:
            lines = [clean_text(line) for line in handle.readlines()]
        seen = set()
        out: List[str] = []
        for line in lines:
            if line and line not in seen:
                out.append(line)
                seen.add(line)
        return out, "partition_prompt_file", args.partition_prompt_file
    return build_partition_texts(seed_df), "seed_csv", None


def build_editor_language_model(config: ModelConfig, corpus_texts: Sequence[str]) -> Any:
    if config.backend == "hf" and config.use_4bit and config.device.lower().startswith("cuda"):
        return EditorSingleGpu4BitHfLanguageModel(config)
    return build_language_model(config, corpus_texts=corpus_texts)


def build_text_units(
    model,
    suffix_text: str,
    payload_blocks: Sequence[Sequence[int]],
    retokenized_buckets: Optional[List[int]],
) -> Tuple[List[TextUnit], List[int]]:
    text_token_ids = [int(x) for x in model.encode(clean_text(suffix_text), add_special_tokens=False)]
    total_payload_bits = sum(len(block) for block in payload_blocks)
    mapping = payload_index_mapping(len(text_token_ids), total_payload_bits)
    units: List[TextUnit] = []
    for idx, token_id in enumerate(text_token_ids):
        payload_index = mapping[idx] if mapping else 0
        block_id, payload_offset = global_payload_pos_to_block_offset(payload_index, len(payload_blocks[0]) if payload_blocks else 7)
        approx_bucket_id = int(retokenized_buckets[idx]) if retokenized_buckets is not None and idx < len(retokenized_buckets) else int(payload_blocks[block_id][payload_offset])
        units.append(
            TextUnit(
                index=idx,
                token_id=int(token_id),
                surface=model.token_surface(int(token_id)),
                block_id=int(block_id),
                payload_index=int(payload_index),
                payload_offset=int(payload_offset),
                approx_bucket_id=int(approx_bucket_id),
            )
        )
    return units, text_token_ids


def build_text_units_from_generated_tokens(
    model,
    token_ids: Sequence[int],
    token_buckets: Sequence[int],
    payload_blocks: Sequence[Sequence[int]],
) -> Tuple[List[TextUnit], List[int], List[int], List[int]]:
    block_len = len(payload_blocks[0]) if payload_blocks else 7
    total_payload_bits = sum(len(block) for block in payload_blocks)
    units: List[TextUnit] = []
    token_block_map: List[int] = []
    token_bucket_ids: List[int] = []
    structural_index = 0
    payload_index = 0
    last_block_id = 0
    for idx, token_id in enumerate(token_ids):
        bucket = int(token_buckets[idx]) if idx < len(token_buckets) else -1
        structural_idx: Optional[int] = None
        if bucket in (0, 1, 2):
            structural_idx = structural_index
            structural_index += 1

        is_payload = bucket in (0, 1) and payload_index < total_payload_bits
        if is_payload:
            block_id, payload_offset = global_payload_pos_to_block_offset(payload_index, block_len)
            last_block_id = max(0, min(block_id, max(0, len(payload_blocks) - 1)))
            unit_payload_index = payload_index
            payload_index += 1
        else:
            block_id = last_block_id
            payload_offset = 0
            unit_payload_index = max(0, min(payload_index, max(0, total_payload_bits - 1)))
            if bucket == 2 and payload_index > 0:
                block_id = max(0, min((payload_index - 1) // block_len, max(0, len(payload_blocks) - 1)))
                last_block_id = block_id

        token_block_map.append(int(block_id))
        token_bucket_ids.append(int(bucket))
        units.append(
            TextUnit(
                index=int(idx),
                token_id=int(token_id),
                surface=model.token_surface(int(token_id)),
                block_id=int(block_id),
                payload_index=int(unit_payload_index),
                payload_offset=int(payload_offset),
                approx_bucket_id=int(bucket),
                structural_index=structural_idx,
                is_payload_token=bool(is_payload),
            )
        )
    return units, [int(x) for x in token_ids], token_block_map, token_bucket_ids


def build_token_block_map_from_units(units: Sequence[TextUnit]) -> List[int]:
    return [int(unit.block_id) for unit in units]


def build_edited_token_block_map(
    original_text_token_ids: Sequence[int],
    original_token_block_map: Sequence[int],
    validated: Sequence[ValidatedInstruction],
) -> List[int]:
    inserts_after: Dict[int, List[int]] = {}
    subs_at: Dict[int, List[int]] = {}
    dels_at: set[int] = set()
    for item in validated:
        if item.op == "insert" and item.gap_after is not None:
            block_id = int(item.structural_anchor.get("block_id", 0))
            inserts_after.setdefault(int(item.gap_after), []).extend([block_id] * len(item.tokenized_new_ids))
        elif item.op == "substitute" and item.original_index is not None:
            if int(item.original_index) < len(original_token_block_map):
                block_id = int(original_token_block_map[int(item.original_index)])
            else:
                block_id = int(item.structural_anchor.get("block_id", 0))
            subs_at[int(item.original_index)] = [block_id] * len(item.tokenized_new_ids)
        elif item.op == "delete" and item.original_index is not None:
            dels_at.add(int(item.original_index))

    edited_block_map: List[int] = []
    edited_block_map.extend(inserts_after.get(-1, []))
    for idx, _token_id in enumerate(original_text_token_ids):
        if idx in dels_at:
            pass
        elif idx in subs_at:
            edited_block_map.extend(subs_at[idx])
        else:
            if idx < len(original_token_block_map):
                edited_block_map.append(int(original_token_block_map[idx]))
        edited_block_map.extend(inserts_after.get(idx, []))
    return edited_block_map


def build_block_text_spans(
    token_ids: Sequence[int],
    token_block_map: Sequence[int],
    model,
    num_blocks: int = 18,
) -> Dict[str, str]:
    grouped: Dict[int, List[int]] = {block_id: [] for block_id in range(int(num_blocks))}
    for token_id, block_id in zip(token_ids, token_block_map):
        block_id = int(block_id)
        if 0 <= block_id < int(num_blocks):
            grouped[block_id].append(int(token_id))
    return {
        str(block_id): model.decode(grouped[block_id], skip_special_tokens=True) if grouped[block_id] else ""
        for block_id in range(int(num_blocks))
    }


def build_token_bucket_ids_from_units(units: Sequence[TextUnit]) -> List[int]:
    return [int(unit.approx_bucket_id) for unit in units]


def build_edited_token_bucket_ids(
    original_token_bucket_ids: Sequence[int],
    validated: Sequence[ValidatedInstruction],
) -> List[int]:
    inserts_after: Dict[int, List[int]] = {}
    subs_at: Dict[int, List[int]] = {}
    dels_at: set[int] = set()
    for item in validated:
        if item.op == "insert" and item.gap_after is not None:
            inserts_after.setdefault(int(item.gap_after), []).extend(int(x) for x in item.mapped_new_buckets)
        elif item.op == "substitute" and item.original_index is not None:
            subs_at[int(item.original_index)] = [int(x) for x in item.mapped_new_buckets]
        elif item.op == "delete" and item.original_index is not None:
            dels_at.add(int(item.original_index))

    edited_bucket_ids: List[int] = []
    edited_bucket_ids.extend(inserts_after.get(-1, []))
    for idx, bucket_id in enumerate(original_token_bucket_ids):
        if idx in dels_at:
            pass
        elif idx in subs_at:
            edited_bucket_ids.extend(subs_at[idx])
        else:
            edited_bucket_ids.append(int(bucket_id))
        edited_bucket_ids.extend(inserts_after.get(idx, []))
    return edited_bucket_ids


def build_edited_token_structural_metadata(
    edited_token_ids: Sequence[int],
    edited_token_block_map: Sequence[int],
    edited_token_bucket_ids: Sequence[int],
    observed_payload_blocks: Sequence[Sequence[int]],
    boundary_symbol: int = 2,
) -> Tuple[List[int], List[int], List[int]]:
    edited_structural_sequence = flatten_payload_blocks_with_boundaries(observed_payload_blocks, boundary_symbol=boundary_symbol)
    block_start_indices: List[int] = []
    cursor = 0
    for block in observed_payload_blocks:
        block_start_indices.append(cursor)
        cursor += len(block) + 1

    edited_token_structural_symbols: List[int] = [-1] * len(edited_token_ids)
    edited_token_structural_indices: List[int] = [-1] * len(edited_token_ids)
    grouped_positions: Dict[int, List[int]] = {}
    for token_pos, block_id in enumerate(edited_token_block_map):
        try:
            block_id_i = int(block_id)
        except Exception:
            continue
        if 0 <= block_id_i < len(observed_payload_blocks):
            grouped_positions.setdefault(block_id_i, []).append(token_pos)

    for block_id, token_positions in grouped_positions.items():
        obs_block = [int(x) for x in observed_payload_blocks[block_id]]
        if not obs_block:
            continue
        num_obs = len(obs_block)
        num_tok = len(token_positions)
        for rank, token_pos in enumerate(token_positions):
            local_pos = min(num_obs - 1, int((rank * num_obs) / max(1, num_tok)))
            edited_token_structural_indices[token_pos] = int(block_start_indices[block_id] + local_pos)
            edited_token_structural_symbols[token_pos] = int(obs_block[local_pos])

    for idx in range(len(edited_token_structural_symbols)):
        if edited_token_structural_symbols[idx] < 0 and idx < len(edited_token_bucket_ids):
            edited_token_structural_symbols[idx] = int(edited_token_bucket_ids[idx])

    return edited_token_structural_symbols, edited_token_structural_indices, edited_structural_sequence


def split_structural_seq_with_positions(seq: Sequence[int], boundary_symbol: int = 2) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    cur: List[int] = []
    cur_start: Optional[int] = None
    for idx, sym in enumerate(seq):
        if int(sym) == int(boundary_symbol):
            if cur_start is None:
                segments.append(
                    {
                        "tokens": [],
                        "token_start": idx,
                        "token_end_exclusive": idx,
                        "ended_with_boundary": True,
                        "boundary_index": idx,
                    }
                )
            else:
                segments.append(
                    {
                        "tokens": cur.copy(),
                        "token_start": cur_start,
                        "token_end_exclusive": idx,
                        "ended_with_boundary": True,
                        "boundary_index": idx,
                    }
                )
            cur = []
            cur_start = None
        else:
            if cur_start is None:
                cur_start = idx
            cur.append(int(sym))
    if cur or (len(seq) > 0 and int(seq[-1]) != int(boundary_symbol)):
        segments.append(
            {
                "tokens": cur.copy(),
                "token_start": int(cur_start if cur_start is not None else len(seq)),
                "token_end_exclusive": len(seq),
                "ended_with_boundary": False,
                "boundary_index": None,
            }
        )
    return segments


def build_detector_block_details(
    pred_blocks: Sequence[Any],
    observed_sequence: Sequence[int],
    tolerance: int,
    codebook: EccCodebook,
    boundary_symbol: int = 2,
) -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for pred_idx, pb in enumerate(pred_blocks):
        start = pb.info.get("observed_span_start")
        end = pb.info.get("observed_span_end_exclusive")
        span = None
        observed_segment = [int(x) for x in pb.block_tokens]
        if start is not None and end is not None:
            start = max(0, int(start))
            end = max(start, min(int(end), len(observed_sequence)))
            span = {"start": start, "end_exclusive": end}
            observed_segment = [int(x) for x in observed_sequence[start:end]]
        details.append(
            {
                "parsed_block_index": int(pred_idx),
                "segment_index": None,
                "exceeds_tolerance": bool(parsed_block_exceeds_tolerance(pb, tolerance=tolerance, codebook=codebook)),
                "observed_structural_span": span,
                "observed_structural_segment": observed_segment,
                "observed_payload_tokens": [int(x) for x in pb.block_tokens],
                "decoded_codeword": [int(x) for x in pb.decoded_codeword] if pb.decoded_codeword is not None else None,
                "candidate_edit_locations": [[str(loc[0]), int(loc[1])] for loc in pb.candidates],
                "is_boundary_edited": bool(pb.is_boundary_edited),
                "boundary_edit_type": pb.boundary_edit_type,
                "ended_with_boundary": pb.info.get("ended_with_boundary"),
                "actual_boundary_following_index": pb.info.get("observed_boundary_index"),
                "payload_distance": pb.info.get("payload_distance"),
                "total_distance": pb.info.get("total_distance"),
                "boundary_state": pb.info.get("boundary_state"),
                "info": to_jsonable(pb.info),
            }
        )
    return details


def build_detector_aligned_block_text_spans(
    edited_token_ids: Sequence[int],
    edited_token_structural_indices: Sequence[int],
    detector_block_details: Sequence[Dict[str, Any]],
    model,
) -> Tuple[Dict[str, str], List[int]]:
    grouped: Dict[int, List[int]] = {int(detail["parsed_block_index"]): [] for detail in detector_block_details}
    token_detector_block_map: List[int] = [-1] * len(edited_token_ids)
    for token_pos, structural_idx in enumerate(edited_token_structural_indices):
        try:
            structural_idx_i = int(structural_idx)
        except Exception:
            continue
        if structural_idx_i < 0:
            continue
        assigned = -1
        for detail in detector_block_details:
            span = detail.get("observed_structural_span")
            if not isinstance(span, dict):
                continue
            start = int(span.get("start", -1))
            end = int(span.get("end_exclusive", -1))
            if start <= structural_idx_i < end:
                assigned = int(detail["parsed_block_index"])
                break
        token_detector_block_map[token_pos] = assigned
        if assigned >= 0:
            grouped.setdefault(assigned, []).append(int(edited_token_ids[token_pos]))

    spans = {
        str(block_id): model.decode(grouped.get(block_id, []), skip_special_tokens=True) if grouped.get(block_id, []) else ""
        for block_id in sorted(grouped.keys())
    }
    return spans, token_detector_block_map


def format_text_unit_table(units: Sequence[TextUnit], max_rows: int = 180) -> str:
    rows = ["index | token_surface | block_id | payload_index | bucket_id | structural_index"]
    for unit in list(units)[:max_rows]:
        surface = unit.surface.replace("\n", " ").replace("\r", " ")
        structural_index = "" if unit.structural_index is None else str(unit.structural_index)
        rows.append(f"{unit.index} | {surface} | {unit.block_id} | {unit.payload_index} | {unit.approx_bucket_id} | {structural_index}")
    if len(units) > max_rows:
        rows.append(f"... truncated {len(units) - max_rows} additional rows ...")
    return "\n".join(rows)


def build_editor_prompt(
    prompt: str,
    suffix_text: str,
    motivation: str,
    intent_label: str,
    units: Sequence[TextUnit],
    max_edited_blocks: int,
    min_edit_instructions: int = 1,
    max_edit_instructions: int = 2,
    aggressive_malicious_edits: bool = False,
    question_aware: bool = False,
    retry_feedback: Optional[str] = None,
) -> str:
    question_aware_block = ""
    if question_aware:
        if intent_label == "malicious" and aggressive_malicious_edits:
            malicious_guidance = (
                "- For malicious motivations, act as a worst-case adversarial editor. Use local edits to make the answer materially misleading while keeping it plausible and not rewriting the whole answer.\n"
                "- Prefer high-impact manipulations: reverse or weaken important factual claims; change quantities, dates, named entities, technical terms, causal relations, safety/risk implications, stance, certainty, or source authority.\n"
                "- Avoid trivial spelling-only, formatting-only, or surface-artifact edits unless they materially change meaning.\n"
            )
        else:
            malicious_guidance = (
                "- For malicious motivations, do not fix surface artifacts; target how the answer responds to the question by altering certainty, attribution, stance, quantities, definitions, causal claims, or source credibility when appropriate.\n"
                "- Keep the edit subtle and local, so the final answer remains mostly fluent and plausible.\n"
            )
        question_aware_block = (
            "Question-aware editing objective:\n"
            "- Treat the source prompt as the question and the source suffix text as its answer.\n"
            "- Make sparse local edits to the answer, not a full rewrite.\n"
            "- The source answer may contain watermark-induced spacing, spelling, or glued-word artifacts; ignore those artifacts unless the motivation explicitly asks for grammar polish.\n"
            "- For benign motivations, improve local wording while preserving factual claims, quantities, entities, causal relations, certainty, stance, risk implications, source attribution, and how the answer responds to the question.\n"
            f"{malicious_guidance}\n"
        )
    retry_block = ""
    if retry_feedback:
        retry_block = (
            "Correction required after an invalid previous attempt:\n"
            f"- {retry_feedback}\n"
            "- Return a complete replacement JSON object, not a patch or explanation.\n\n"
        )
    return (
        "You are a sparse text editor for watermark robustness experiments.\n"
        "Return JSON only. Do not rewrite the whole text.\n"
        f"Motivation: {motivation}\n"
        f"Intent label: {intent_label}\n"
        "Allowed ops: substitute, delete, insert.\n"
        f"Return between {min_edit_instructions} and {max_edit_instructions} edit objects whenever possible, and keep the total affected blocks below {max_edited_blocks}.\n"
        f"Do not stop after only a few edits unless fewer than {min_edit_instructions} valid local edit opportunities exist in the table.\n"
        "For substitute/delete, choose an index from a table row whose bucket_id is 0, 1, or 2, and copy original_text exactly from that row's token_surface; do not write the full word if the table shows only a subword token.\n"
        "STRICT NO-OP RULE: every substitute must change the selected token. After trimming and normalizing whitespace, new_content must not equal original_text.\n"
        "Before returning JSON, compare every substitute's original_text and new_content. If they are identical, choose a genuinely different replacement, choose another token index, or use delete/insert instead.\n"
        "A single unchanged substitute makes the entire response invalid; never use a substitute merely to reach the requested edit count.\n"
        "For insert, use gap_after from the table index after which the new content should be inserted.\n"
        "Never use blank-only new_content such as a single space; new_content must contain meaningful English words or punctuation plus words.\n"
        "Do not produce commentary outside JSON.\n\n"
        f"{retry_block}"
        f"{question_aware_block}"
        "Source prompt:\n"
        f"{prompt}\n\n"
        "Source suffix text to edit:\n"
        f"{suffix_text}\n\n"
        "Indexed edit-unit table:\n"
        f"{format_text_unit_table(units)}\n\n"
        "Return this schema exactly:\n"
        "{\n"
        '  "motivation": "...",\n'
        '  "intent_label": "...",\n'
        '  "edits": [\n'
        '    {"op": "substitute", "index": 0, "original_text": "...", "new_content": "...", "reason": "..."},\n'
        '    {"op": "delete", "index": 0, "original_text": "...", "reason": "..."},\n'
        '    {"op": "insert", "gap_after": 0, "new_content": "...", "reason": "..."}\n'
        "  ]\n"
        "}\n"
    )


def retry_feedback_for_error(error: str) -> str:
    messages = {
        "substitute_no_text_change": (
            "At least one substitute used the same normalized text as the selected "
            "original token. Replace it with different content or choose a different "
            "operation/index."
        ),
        "invalid_json": (
            "The response was not valid parseable JSON. Return exactly one JSON object "
            "with no prose or Markdown fences."
        ),
        "original_text_mismatch": (
            "At least one original_text value did not exactly copy the token_surface "
            "from its selected table row. Copy the displayed token surface verbatim."
        ),
        "too_many_edit_instructions": (
            "The edits list exceeded max_edit_instructions. Return no more than the "
            "allowed maximum."
        ),
        "substitute_missing_new_content": (
            "At least one substitute omitted meaningful new_content."
        ),
    }
    return messages.get(error, f"The previous response failed validation: {error}.")


def prepare_resume_records(
    detail_rows: Sequence[Dict[str, Any]],
    instruction_records: Sequence[Dict[str, Any]],
    retry_skipped: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], set]:
    if retry_skipped:
        retained_details = [
            dict(item)
            for item in detail_rows
            if str(item.get("used", "")).strip().lower() in {"true", "1"}
        ]
    else:
        retained_details = [dict(item) for item in detail_rows]
    completed_keys = {
        (int(item["sequence_index"]), str(item["motivation"]))
        for item in retained_details
    }
    retained_instructions = [
        dict(item)
        for item in instruction_records
        if (int(item["sequence_index"]), str(item["motivation"])) in completed_keys
    ]
    return retained_details, retained_instructions, completed_keys


def choose_surface_from_bucket(model, partition: VocabularyPartition, bucket_id: int, fallback: str) -> str:
    candidate_ids = partition.bucket1_ids if int(bucket_id) == 1 else partition.bucket0_ids
    if not candidate_ids:
        return fallback
    return model.token_surface(int(candidate_ids[0]))


def mock_editor_response(units: Sequence[TextUnit], motivation: str, intent_label: str, model, partition: VocabularyPartition) -> str:
    if not units:
        return json.dumps({"motivation": motivation, "intent_label": intent_label, "edits": []})
    first = units[min(1, len(units) - 1)]
    middle = units[len(units) // 2]
    first_replacement = choose_surface_from_bucket(model, partition, 1 - int(first.approx_bucket_id), fallback=" clearly")
    middle_replacement = choose_surface_from_bucket(model, partition, 1 - int(middle.approx_bucket_id), fallback=" however")
    insert_replacement = choose_surface_from_bucket(model, partition, 1 - int(middle.approx_bucket_id), fallback=" not")
    if motivation == "grammar_polish":
        edits = [
            {
                "op": "substitute",
                "index": int(first.index),
                "original_text": first.surface,
                "new_content": first_replacement,
                "reason": "small fluency adjustment",
            }
        ]
    elif motivation == "claim_distortion":
        edits = [
            {
                "op": "insert",
                "gap_after": int(middle.index),
                "new_content": insert_replacement,
                "reason": "subtle factual distortion",
            },
            {
                "op": "substitute",
                "index": int(first.index),
                "original_text": first.surface,
                "new_content": first_replacement,
                "reason": "shift certainty",
            },
        ]
    else:
        edits = [
            {
                "op": "substitute",
                "index": int(middle.index),
                "original_text": middle.surface,
                "new_content": middle_replacement,
                "reason": "local style change",
            }
        ]
    return json.dumps({"motivation": motivation, "intent_label": intent_label, "edits": edits}, ensure_ascii=False)


def hf_editor_response(editor_model: HfLanguageModel, editor_prompt: str, max_new_tokens: int, enable_thinking: bool = False) -> str:
    tokenizer = editor_model.tokenizer
    model = editor_model.model
    device = editor_model.device
    if hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": "Return JSON only. Do not include markdown fences or extra text."},
            {"role": "user", "content": editor_prompt},
        ]
        try:
            encoded = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                enable_thinking=bool(enable_thinking),
            )
        except TypeError:
            encoded = tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
            )
        encoded = encoded.to(device)
        if not hasattr(encoded, "keys"):
            encoded = {"input_ids": encoded}
    else:
        encoded = tokenizer(editor_prompt, return_tensors="pt", add_special_tokens=True).to(device)
    generation_kwargs = {
        "max_new_tokens": int(max_new_tokens),
        "do_sample": False,
        "pad_token_id": int(tokenizer.pad_token_id),
        "eos_token_id": int(tokenizer.eos_token_id) if tokenizer.eos_token_id is not None else None,
    }
    if any(
        generation_kwargs.get(key) is not None
        for key in ("temperature", "top_p", "top_k")
    ):
        generation_kwargs["do_sample"] = True
    outputs = model.generate(**encoded, **generation_kwargs)
    input_len = encoded["input_ids"].shape[-1]
    new_tokens = outputs[0, input_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def tokenize_new_content(model, text: str) -> List[int]:
    return [int(x) for x in model.encode(clean_text(text), add_special_tokens=False)]


def map_token_ids_to_structural_symbols(
    token_ids: Sequence[int],
    partition: VocabularyPartition,
) -> List[int]:
    symbols: List[int] = []
    for token_id in token_ids:
        token_id = int(token_id)
        bucket = (
            int(partition.token_to_bucket[token_id])
            if 0 <= token_id < len(partition.token_to_bucket)
            else -1
        )
        if bucket not in (0, 1, 2):
            raise ValueError(f"Token id {token_id} is excluded from the structural partition.")
        symbols.append(bucket)
    return symbols


def local_window_for_index(text_token_ids: Sequence[int], model, index: int, radius: int = 1) -> str:
    start = max(0, int(index) - radius)
    end = min(len(text_token_ids), int(index) + radius + 1)
    return model.decode(text_token_ids[start:end], skip_special_tokens=True)


def build_exact_reconstruction_info(
    suffix_text: str,
    model,
    partition: VocabularyPartition,
    saved_bucket_sequence: Sequence[int],
) -> Dict[str, Any]:
    retokenized_ids = [int(x) for x in model.encode(clean_text(suffix_text), add_special_tokens=False)]
    retokenized_buckets = [
        int(partition.token_to_bucket[token_id]) if token_id < len(partition.token_to_bucket) else -1
        for token_id in retokenized_ids
    ]
    saved = [int(x) for x in saved_bucket_sequence]
    compare_len = min(len(saved), len(retokenized_buckets))
    matches = sum(1 for i in range(compare_len) if saved[i] == retokenized_buckets[i])
    exact = len(saved) == len(retokenized_buckets) and matches == len(saved)
    return {
        "retokenized_token_ids": retokenized_ids,
        "retokenized_buckets": retokenized_buckets,
        "saved_bucket_sequence": saved,
        "exact_match": bool(exact),
        "compare_len": int(compare_len),
        "match_count": int(matches),
        "match_rate": float(matches / compare_len) if compare_len > 0 else math.nan,
    }


def validate_saved_bucket_sequence_against_partition(
    *,
    token_ids: Sequence[int],
    saved_bucket_sequence: Sequence[int],
    partition: VocabularyPartition,
    sequence_index: int,
) -> Dict[str, Any]:
    """Ensure a seed row's saved bucket sequence came from the loaded partition."""
    loaded_buckets = [
        int(partition.token_to_bucket[int(token_id)]) if int(token_id) < len(partition.token_to_bucket) else -1
        for token_id in token_ids
    ]
    saved = [int(x) for x in saved_bucket_sequence]
    compare_len = min(len(saved), len(loaded_buckets))
    mismatches = [
        {
            "position": int(i),
            "token_id": int(token_ids[i]),
            "saved_bucket": int(saved[i]),
            "loaded_bucket": int(loaded_buckets[i]),
        }
        for i in range(compare_len)
        if int(saved[i]) != int(loaded_buckets[i])
    ]
    length_match = len(saved) == len(loaded_buckets)
    if mismatches or not length_match:
        preview = mismatches[:10]
        raise RuntimeError(
            "Seed token/bucket sequence is inconsistent with --partition-dir. "
            f"sequence_index={sequence_index} saved_len={len(saved)} token_len={len(loaded_buckets)} "
            f"mismatch_count={len(mismatches)} first_mismatches={preview}. "
            "Regenerate the source text with this exact partition before running the editor."
        )
    return {
        "partition_bucket_exact_match": True,
        "partition_bucket_compare_len": int(compare_len),
        "partition_bucket_mismatch_count": 0,
    }


def validate_and_translate_instructions(
    parsed_json: Dict[str, Any],
    motivation: str,
    intent_label: str,
    units: Sequence[TextUnit],
    text_token_ids: Sequence[int],
    original_payload_blocks: Sequence[Sequence[int]],
    partition: VocabularyPartition,
    model,
    max_edited_blocks: int,
    min_edit_instructions: int = 1,
    max_edit_instructions: int = 2,
    max_block_edit_rate: float = 0.5,
) -> Tuple[List[ValidatedInstruction], Optional[str]]:
    if not isinstance(parsed_json, dict):
        return [], "json_not_dict"
    edits = parsed_json.get("edits")
    if not isinstance(edits, list) or len(edits) == 0:
        return [], "missing_or_empty_edits"
    if len(edits) < int(min_edit_instructions):
        return [], "too_few_edit_instructions"
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
        if op == "substitute" and normalize_text_match(original_text) == normalize_text_match(new_content):
            return [], "substitute_no_text_change"
        tokenized_new_ids = tokenize_new_content(model, new_content) if op in {"substitute", "insert"} else []
        try:
            mapped_new_buckets = (
                map_token_ids_to_structural_symbols(tokenized_new_ids, partition)
                if op in {"substitute", "insert"}
                else []
            )
        except ValueError:
            return [], "new_content_contains_excluded_token"

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
            text_pos_anchors.add(idx)
            block_id = int(unit.block_id)
            if unit.is_payload_token and int(unit.approx_bucket_id) in (0, 1):
                payload_pos = int(unit.payload_index)
                if payload_pos in payload_pos_anchors:
                    return [], "duplicate_payload_position"
                payload_pos_anchors.add(payload_pos)
                block_id, payload_offset = global_payload_pos_to_block_offset(payload_pos, block_len)
                event_loc = ("payload", payload_offset)
                anchor_type = "payload_position"
                structural_anchor = {
                    "type": anchor_type,
                    "global_payload_index": payload_pos,
                    "block_id": block_id,
                    "payload_offset": payload_offset,
                    "structural_index": unit.structural_index,
                }
            else:
                payload_offset = block_len
                event_loc = ("boundary", block_len)
                anchor_type = "boundary_position"
                structural_anchor = {
                    "type": anchor_type,
                    "block_id": block_id,
                    "payload_offset": block_len,
                    "structural_index": unit.structural_index,
                }

            if op == "substitute":
                if not tokenized_new_ids or not mapped_new_buckets:
                    return [], "substitute_missing_new_content"
                original_symbol = int(unit.approx_bucket_id)
                replacement_symbols = [int(x) for x in mapped_new_buckets]
                block_events = {
                    block_id: [
                        EditEvent(
                            "sub",
                            event_loc,
                            value_before=original_symbol,
                            value_after=replacement_symbols[0],
                        )
                    ]
                }
                if len(replacement_symbols) > 1:
                    block_events[block_id].extend(
                        EditEvent(
                            "insert",
                            ("gap", min(block_len, payload_offset + 1)),
                            value_after=int(symbol),
                        )
                        for symbol in replacement_symbols[1:]
                    )
                affected_blocks = [block_id]
            else:
                block_events = {
                    block_id: [
                        EditEvent(
                            "delete",
                            event_loc,
                            value_before=int(unit.approx_bucket_id),
                        )
                    ]
                }
                affected_blocks = [block_id]
            validated.append(
                ValidatedInstruction(
                    op=op,
                    original_index=idx,
                    gap_after=None,
                    original_text=original_text,
                    new_content=new_content,
                    reason=reason,
                    tokenized_new_ids=tokenized_new_ids,
                    mapped_new_buckets=mapped_new_buckets,
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
            if not tokenized_new_ids or not mapped_new_buckets:
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
                block_id: [
                    EditEvent("insert", ("gap", gap_offset), value_after=int(symbol))
                    for symbol in mapped_new_buckets
                ]
            }
            affected_blocks = [block_id]
            validated.append(
                ValidatedInstruction(
                    op=op,
                    original_index=None,
                    gap_after=gap_after,
                    original_text=original_text,
                    new_content=new_content,
                    reason=reason,
                    tokenized_new_ids=tokenized_new_ids,
                    mapped_new_buckets=mapped_new_buckets,
                    affected_blocks=affected_blocks,
                    block_events=block_events,
                    structural_anchor={
                        "type": "payload_gap",
                        "global_gap_index": gap_global,
                        "block_id": block_id,
                        "gap_offset": gap_offset,
                        "structural_index": (
                            index_to_unit[gap_after].structural_index if gap_after >= 0 else -1
                        ),
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


def apply_validated_structural_edits(
    original_payload_blocks: Sequence[Sequence[int]],
    validated: Sequence[ValidatedInstruction],
) -> Tuple[List[int], List[List[EditEvent]], List[int]]:
    block_len = len(original_payload_blocks[0]) if original_payload_blocks else 7
    num_blocks = len(original_payload_blocks)
    sub_ops: Dict[Tuple[int, int], List[int]] = {}
    del_ops: Dict[Tuple[int, int], bool] = {}
    insert_ops: Dict[Tuple[int, int], List[int]] = {}
    gt_events_per_block: List[List[EditEvent]] = [[] for _ in range(num_blocks)]

    for item in validated:
        for block_id, events in item.block_events.items():
            gt_events_per_block[block_id].extend(events)
            for ev in events:
                loc_kind, loc_idx = ev.loc
                if ev.etype == "sub" and loc_kind == "payload":
                    sub_ops[(block_id, int(loc_idx))] = [int(ev.value_after)]
                elif ev.etype == "delete" and loc_kind == "payload":
                    del_ops[(block_id, int(loc_idx))] = True
                elif ev.etype == "insert" and loc_kind == "gap":
                    insert_ops.setdefault((block_id, int(loc_idx)), []).append(int(ev.value_after))

    observed_payload_blocks: List[List[int]] = []
    observed_sequence: List[int] = []
    for block_id, block in enumerate(original_payload_blocks):
        cur: List[int] = []
        cur.extend(insert_ops.get((block_id, 0), []))
        for payload_offset, bit in enumerate(block):
            if (block_id, payload_offset) in del_ops:
                pass
            elif (block_id, payload_offset) in sub_ops:
                cur.append(int(sub_ops[(block_id, payload_offset)][0]))
            else:
                cur.append(int(bit))
            cur.extend(insert_ops.get((block_id, payload_offset + 1), []))
        observed_payload_blocks.append(cur)
        observed_sequence.extend(cur)
        observed_sequence.append(2)
    return observed_payload_blocks, gt_events_per_block, observed_sequence


def apply_validated_text_edits(
    original_text_token_ids: Sequence[int],
    validated: Sequence[ValidatedInstruction],
) -> List[int]:
    inserts_after: Dict[int, List[int]] = {}
    subs_at: Dict[int, List[int]] = {}
    dels_at: set[int] = set()
    for item in validated:
        if item.op == "insert" and item.gap_after is not None:
            inserts_after.setdefault(int(item.gap_after), []).extend(int(x) for x in item.tokenized_new_ids)
        elif item.op == "substitute" and item.original_index is not None:
            subs_at[int(item.original_index)] = [int(x) for x in item.tokenized_new_ids]
        elif item.op == "delete" and item.original_index is not None:
            dels_at.add(int(item.original_index))

    edited: List[int] = []
    edited.extend(inserts_after.get(-1, []))
    for idx, token_id in enumerate(original_text_token_ids):
        if idx in dels_at:
            pass
        elif idx in subs_at:
            edited.extend(subs_at[idx])
        else:
            edited.append(int(token_id))
        edited.extend(inserts_after.get(idx, []))
    return edited


def build_gt_events_from_validated(
    validated: Sequence[ValidatedInstruction],
    num_blocks: int,
) -> List[List[EditEvent]]:
    gt_events_per_block: List[List[EditEvent]] = [[] for _ in range(int(num_blocks))]
    for item in validated:
        for block_id, events in item.block_events.items():
            if 0 <= int(block_id) < len(gt_events_per_block):
                gt_events_per_block[int(block_id)].extend(events)
    return gt_events_per_block


def apply_validated_token_edits_with_provenance(
    original_text_token_ids: Sequence[int],
    units: Sequence[TextUnit],
    validated: Sequence[ValidatedInstruction],
    partition: VocabularyPartition,
) -> Tuple[List[int], List[int], List[Dict[str, Any]]]:
    unit_by_index = {int(unit.index): unit for unit in units}
    inserts_after: Dict[int, List[ValidatedInstruction]] = {}
    substitutes_at: Dict[int, ValidatedInstruction] = {}
    deletes_at: set[int] = set()
    for item in validated:
        if item.op == "insert" and item.gap_after is not None:
            inserts_after.setdefault(int(item.gap_after), []).append(item)
        elif item.op == "substitute" and item.original_index is not None:
            substitutes_at[int(item.original_index)] = item
        elif item.op == "delete" and item.original_index is not None:
            deletes_at.add(int(item.original_index))

    edited_ids: List[int] = []
    provenance: List[Dict[str, Any]] = []

    def append_instruction_tokens(item: ValidatedInstruction, origin: str) -> None:
        block_id = int(item.structural_anchor.get("block_id", 0))
        anchor_structural_index = item.structural_anchor.get("structural_index")
        for replacement_offset, token_id in enumerate(item.tokenized_new_ids):
            edited_ids.append(int(token_id))
            provenance.append(
                {
                    "origin": origin,
                    "original_token_index": item.original_index,
                    "gap_after": item.gap_after,
                    "original_block_id": block_id,
                    "original_structural_index": anchor_structural_index,
                    "replacement_offset": int(replacement_offset),
                }
            )

    for item in inserts_after.get(-1, []):
        append_instruction_tokens(item, "insert")
    for idx, token_id in enumerate(original_text_token_ids):
        unit = unit_by_index.get(idx)
        if idx in deletes_at:
            pass
        elif idx in substitutes_at:
            append_instruction_tokens(substitutes_at[idx], "substitute")
        else:
            edited_ids.append(int(token_id))
            provenance.append(
                {
                    "origin": "unchanged",
                    "original_token_index": int(idx),
                    "gap_after": None,
                    "original_block_id": int(unit.block_id) if unit is not None else None,
                    "original_structural_index": (
                        unit.structural_index if unit is not None else None
                    ),
                    "replacement_offset": None,
                }
            )
        for item in inserts_after.get(idx, []):
            append_instruction_tokens(item, "insert")

    expected_ids = apply_validated_text_edits(original_text_token_ids, validated)
    if edited_ids != expected_ids:
        raise RuntimeError("Exact token-edit replay disagrees with apply_validated_text_edits.")
    structural_symbols = map_token_ids_to_structural_symbols(edited_ids, partition)
    if len(structural_symbols) != len(provenance):
        raise RuntimeError("Edited structural sequence and provenance lengths disagree.")
    for structural_index, (symbol, item) in enumerate(zip(structural_symbols, provenance)):
        item["edited_structural_index"] = int(structural_index)
        item["edited_structural_symbol"] = int(symbol)
    return edited_ids, structural_symbols, provenance


def editor_backend_generate(
    editor_backend: str,
    editor_model,
    base_model,
    partition: VocabularyPartition,
    editor_prompt: str,
    units: Sequence[TextUnit],
    motivation: str,
    intent_label: str,
    max_new_tokens: int,
    editor_enable_thinking: bool = False,
) -> str:
    if editor_backend == "mock":
        return mock_editor_response(units=units, motivation=motivation, intent_label=intent_label, model=base_model, partition=partition)
    if editor_backend == "hf":
        if not isinstance(editor_model, HfLanguageModel):
            raise RuntimeError("HF editor backend requires an HfLanguageModel.")
        return hf_editor_response(editor_model, editor_prompt, max_new_tokens=max_new_tokens, enable_thinking=editor_enable_thinking)
    raise ValueError(f"Unsupported editor_backend: {editor_backend}")


def finite_or_nan(num: float, den: float) -> float:
    if den == 0:
        return math.nan
    return float(num) / float(den)


def build_summary_dataframe(detail_rows: Sequence[Dict[str, Any]]) -> pd.DataFrame:
    if not detail_rows:
        return pd.DataFrame(
            columns=[
                "motivation",
                "intent_label",
                "num_samples_total",
                "num_samples_used",
                "skipped_count",
                "mean_edited_blocks",
                "mean_block_edit_rate",
                "TP",
                "FP",
                "FN",
                "TN",
                "block_tpr",
                "block_far",
                "candidate_coverage",
            ]
        )
    detail_df = pd.DataFrame(detail_rows)
    summary_rows: List[Dict[str, Any]] = []
    for (motivation, intent_label), group in detail_df.groupby(["motivation", "intent_label"], dropna=False):
        used_group = group[group["used"] == True]  # noqa: E712
        tp = int(used_group["TP"].sum()) if not used_group.empty else 0
        fp = int(used_group["FP"].sum()) if not used_group.empty else 0
        fn = int(used_group["FN"].sum()) if not used_group.empty else 0
        tn = int(used_group["TN"].sum()) if not used_group.empty else 0
        used_count = int(len(used_group))
        candidate_hit_total = float(used_group["event_loc_hit"].sum()) if not used_group.empty else 0.0
        candidate_event_total = float(used_group["event_total_overall"].sum()) if not used_group.empty else 0.0
        summary_rows.append(
            {
                "motivation": motivation,
                "intent_label": intent_label,
                "num_samples_total": int(len(group)),
                "num_samples_used": used_count,
                "skipped_count": int(len(group) - used_count),
                "mean_edited_blocks": float(used_group["num_edited_blocks"].mean()) if used_count > 0 else math.nan,
                "mean_block_edit_rate": float(used_group["block_edit_rate"].mean()) if used_count > 0 else math.nan,
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "TN": tn,
                "block_tpr": finite_or_nan(tp, tp + fn),
                "block_far": finite_or_nan(fp, fp + tn),
                "candidate_coverage": finite_or_nan(candidate_hit_total, candidate_event_total),
            }
        )
    return pd.DataFrame(summary_rows).sort_values(["intent_label", "motivation"]).reset_index(drop=True)


def write_checkpoint(
    output_dir: str,
    detail_rows: Sequence[Dict[str, Any]],
    instruction_records: Sequence[Dict[str, Any]],
    total_expected_rows: int,
) -> None:
    checkpoint_dir = Path(output_dir)
    detail_df = pd.DataFrame(detail_rows)
    summary_df = build_summary_dataframe(detail_rows)
    save_dataframe(summary_df, str(checkpoint_dir / "llm_editor_summary_checkpoint"), save_parquet=False)
    save_dataframe(detail_df, str(checkpoint_dir / "llm_editor_details_checkpoint"), save_parquet=False)
    write_json(str(checkpoint_dir / "llm_edit_instructions_checkpoint.json"), list(instruction_records))
    used_count = int(detail_df["used"].sum()) if "used" in detail_df.columns else 0
    write_json(
        str(checkpoint_dir / "llm_editor_progress_checkpoint.json"),
        {
            "processed_rows": int(len(detail_rows)),
            "total_expected_rows": int(total_expected_rows),
            "used_count": used_count,
            "skipped_count": int(len(detail_rows) - used_count),
        },
    )
    print(f"[checkpoint] processed {len(detail_rows)}/{total_expected_rows} rows; used={used_count}", flush=True)


def run_editor_experiment(args: argparse.Namespace) -> Dict[str, Any]:
    ensure_dir(args.output_dir)
    if int(args.min_edit_instructions) < 1:
        raise ValueError("--min-edit-instructions must be at least 1.")
    if int(args.min_edit_instructions) > int(args.max_edit_instructions):
        raise ValueError("--min-edit-instructions cannot exceed --max-edit-instructions.")
    seed_df = load_seed_dataframe(args.seed_csv, args.num_samples)
    if seed_df.empty:
        raise RuntimeError("Seed CSV is empty after filtering.")

    motivations = parse_csv_strs(args.motivations)
    invalid_motivations = [m for m in motivations if m not in ALL_MOTIVATIONS]
    if invalid_motivations:
        raise ValueError(f"Unknown motivations: {invalid_motivations}")

    partition_texts, partition_source, partition_prompt_file = load_partition_texts(args, seed_df)
    if not args.partition_dir and not partition_texts:
        raise RuntimeError("No partition texts were loaded. Provide a valid --partition-prompt-file or a non-empty seed CSV.")
    model_corpus_texts = build_partition_texts(seed_df) or partition_texts
    with open(Path(args.output_dir) / "partition_texts.txt", "w", encoding="utf-8") as handle:
        for text in partition_texts:
            handle.write(clean_text(text) + "\n")

    base_model = build_editor_language_model(
        ModelConfig(
            backend=args.model_backend,
            model_name=args.model_name,
            model_profile=args.model_profile,
            device=args.device,
            max_prompt_tokens=args.max_prompt_tokens,
            use_4bit=args.use_4bit,
            low_cpu_mem_usage=True,
        ),
        corpus_texts=model_corpus_texts,
    )
    if args.editor_backend == "hf":
        if args.model_backend != "hf":
            raise ValueError("editor-backend=hf currently requires model-backend=hf so the same tokenizer/model can be reused.")
        if args.editor_model and args.editor_model != args.model_name:
            editor_model = build_editor_language_model(
                ModelConfig(
                    backend="hf",
                    model_name=args.editor_model,
                    device=args.device,
                    max_prompt_tokens=args.max_prompt_tokens,
                    use_4bit=args.use_4bit,
                    low_cpu_mem_usage=True,
                ),
                corpus_texts=model_corpus_texts,
            )
        else:
            editor_model = base_model
    else:
        editor_model = None

    if args.partition_dir:
        partition = load_vocabulary_partition(args.partition_dir)
        validate_vocabulary_partition(
            partition,
            base_model,
            require_semantic_split=args.require_semantic_partition,
        )
        partition_source = "partition_dir"
    else:
        partition = build_vocabulary_partition(base_model, partition_texts, ECCConfig(block_len=args.block_len, vt_a=args.vt_a))
        save_vocabulary_partition(
            partition,
            Path(args.output_dir) / "partition",
            metadata={
                "partition_source": partition_source,
                "num_partition_texts": len(partition_texts),
            },
        )
    codebook = EccCodebook(block_len=args.block_len, vt_a=args.vt_a)
    decoder_config = EccDecoderConfig(
        decoder_max_edits_per_block=args.decoder_max_edits_per_block,
        boundary_edit_modes=("delete", "sub"),
    )

    detail_rows: List[Dict[str, Any]] = []
    instruction_records: List[Dict[str, Any]] = []
    total_expected_rows = len(seed_df) if args.motivation_assignment == "round_robin" else len(seed_df) * len(motivations)
    completed_keys = set()
    if args.resume:
        resume_dir = Path(args.resume_from_output_dir or args.output_dir)
        detail_checkpoint = resume_dir / "llm_editor_details_checkpoint.csv"
        detail_final = resume_dir / "llm_editor_details.csv"
        instruction_checkpoint = resume_dir / "llm_edit_instructions_checkpoint.json"
        instruction_final = resume_dir / "llm_edit_instructions.json"
        detail_source = (
            detail_final
            if args.retry_skipped and detail_final.exists()
            else detail_checkpoint
        )
        instruction_source = (
            instruction_final
            if args.retry_skipped and instruction_final.exists()
            else instruction_checkpoint
        )
        loaded_detail_rows: List[Dict[str, Any]] = []
        loaded_instruction_records: List[Dict[str, Any]] = []
        if detail_source.exists():
            loaded_detail_rows = pd.read_csv(detail_source).to_dict(orient="records")
        if instruction_source.exists():
            with open(instruction_source, "r", encoding="utf-8") as handle:
                loaded_instructions = json.load(handle)
            if isinstance(loaded_instructions, list):
                loaded_instruction_records = loaded_instructions
        detail_rows, instruction_records, completed_keys = prepare_resume_records(
            loaded_detail_rows,
            loaded_instruction_records,
            retry_skipped=args.retry_skipped,
        )
        if loaded_detail_rows:
            retry_count = len(loaded_detail_rows) - len(detail_rows)
            mode = (
                f"retained {len(detail_rows)} accepted rows and queued "
                f"{retry_count} skipped rows"
                if args.retry_skipped
                else f"loaded {len(detail_rows)} completed rows"
            )
            print(
                f"[resume] {mode} from {resume_dir}",
                flush=True,
            )

    for row_idx, row in seed_df.iterrows():
        sequence_index = int(row["sequence_index"])
        prompt = str(row["prompt"])
        suffix_text = str(row["suffix_text"])
        saved_bucket_seq = parse_bucket_id_sequence(row["bucket_id_sequence"])
        original_payload_blocks = parse_payload_blocks_json(row["block_bucket_sequences_json"])
        saved_token_ids = parse_optional_int_list(row.get("generated_token_ids")) if "generated_token_ids" in row.index else []
        recon = build_exact_reconstruction_info(suffix_text, base_model, partition, saved_bucket_seq)
        if saved_token_ids:
            if args.partition_dir:
                recon.update(
                    validate_saved_bucket_sequence_against_partition(
                        token_ids=saved_token_ids,
                        saved_bucket_sequence=saved_bucket_seq,
                        partition=partition,
                        sequence_index=sequence_index,
                    )
                )
            reconstruction_mode = "saved_generated_token_ids"
            text_units, original_text_token_ids, source_token_block_map, source_token_bucket_ids = build_text_units_from_generated_tokens(
                model=base_model,
                token_ids=saved_token_ids,
                token_buckets=saved_bucket_seq,
                payload_blocks=original_payload_blocks,
            )
            recon["mode"] = reconstruction_mode
            recon["saved_generated_token_ids_len"] = len(saved_token_ids)
        else:
            reconstruction_mode = "retokenized_exact" if recon["exact_match"] else "saved_bucket_sequence_fallback"
            text_units, original_text_token_ids = build_text_units(
                model=base_model,
                suffix_text=suffix_text,
                payload_blocks=original_payload_blocks,
                retokenized_buckets=recon["retokenized_buckets"],
            )
            source_token_block_map = build_token_block_map_from_units(text_units)
            source_token_bucket_ids = build_token_bucket_ids_from_units(text_units)
        if args.motivation_assignment == "round_robin":
            row_motivations = [motivations[int(row_idx) % len(motivations)]]
        else:
            row_motivations = motivations

        for motivation in row_motivations:
            if (sequence_index, motivation) in completed_keys:
                continue
            intent_label = canonical_intent_label(motivation)
            used = False
            skip_reason = None
            accepted_json = None
            pred_blocks_flags: List[int] = []
            gt_blocks_flags: List[int] = []
            summary_payload: Dict[str, Any] = {}
            edited_text = suffix_text
            accepted_instructions: List[ValidatedInstruction] = []
            last_raw_output = ""
            last_parsed_output = None
            original_token_block_map = list(source_token_block_map)
            original_token_bucket_ids = list(source_token_bucket_ids)
            edited_text_token_ids = list(original_text_token_ids)
            edited_token_block_map = list(original_token_block_map)
            edited_token_bucket_ids = list(original_token_bucket_ids)
            edited_token_structural_symbols: List[int] = []
            edited_token_structural_indices: List[int] = []
            unit_by_index = {int(unit.index): unit for unit in text_units}
            edited_token_provenance: List[Dict[str, Any]] = [
                {
                    "origin": "unchanged",
                    "original_token_index": int(index),
                    "gap_after": None,
                    "original_block_id": (
                        int(unit_by_index[index].block_id) if index in unit_by_index else None
                    ),
                    "original_structural_index": (
                        unit_by_index[index].structural_index if index in unit_by_index else None
                    ),
                    "replacement_offset": None,
                    "edited_structural_index": int(index),
                    "edited_structural_symbol": (
                        int(original_token_bucket_ids[index])
                        if index < len(original_token_bucket_ids)
                        else -1
                    ),
                }
                for index in range(len(original_text_token_ids))
            ]
            edited_structural_sequence = flatten_payload_blocks_with_boundaries(original_payload_blocks)
            ev: Dict[str, Any] = {
                "parsed_to_source_blocks": [],
                "source_candidate_locations": [],
            }
            detector_block_details: List[Dict[str, Any]] = []
            detector_aligned_block_text_spans: Dict[str, str] = {}
            edited_token_block_map_from_detector: List[int] = []
            original_block_text_spans = build_block_text_spans(
                original_text_token_ids,
                original_token_block_map,
                base_model,
                num_blocks=len(original_payload_blocks),
            )
            edited_block_text_spans = dict(original_block_text_spans)
            retry_feedback: Optional[str] = None
            for attempt in range(args.max_retries + 1):
                editor_prompt = build_editor_prompt(
                    prompt=prompt,
                    suffix_text=suffix_text,
                    motivation=motivation,
                    intent_label=intent_label,
                    units=text_units,
                    max_edited_blocks=args.max_edited_blocks,
                    min_edit_instructions=args.min_edit_instructions,
                    max_edit_instructions=args.max_edit_instructions,
                    aggressive_malicious_edits=args.aggressive_malicious_edits,
                    question_aware=args.question_aware,
                    retry_feedback=retry_feedback,
                )
                raw_output = editor_backend_generate(
                    editor_backend=args.editor_backend,
                    editor_model=editor_model,
                    base_model=base_model,
                    partition=partition,
                    editor_prompt=editor_prompt,
                    units=text_units,
                    motivation=motivation,
                    intent_label=intent_label,
                    max_new_tokens=args.editor_max_new_tokens,
                    editor_enable_thinking=args.editor_enable_thinking,
                )
                parsed_output = extract_json_object(raw_output)
                last_raw_output = raw_output
                last_parsed_output = parsed_output
                if parsed_output is None:
                    skip_reason = "invalid_json"
                    retry_feedback = retry_feedback_for_error(skip_reason)
                    continue
                validated, validation_error = validate_and_translate_instructions(
                    parsed_json=parsed_output,
                    motivation=motivation,
                    intent_label=intent_label,
                    units=text_units,
                    text_token_ids=original_text_token_ids,
                    original_payload_blocks=original_payload_blocks,
                    partition=partition,
                    model=base_model,
                    max_edited_blocks=args.max_edited_blocks,
                    min_edit_instructions=args.min_edit_instructions,
                    max_edit_instructions=args.max_edit_instructions,
                    max_block_edit_rate=args.max_block_edit_rate,
                )
                if validation_error is not None:
                    skip_reason = validation_error
                    retry_feedback = retry_feedback_for_error(skip_reason)
                    continue
                (
                    edited_text_token_ids,
                    observed_sequence,
                    edited_token_provenance,
                ) = apply_validated_token_edits_with_provenance(
                    original_text_token_ids=original_text_token_ids,
                    units=text_units,
                    validated=validated,
                    partition=partition,
                )
                gt_events_per_block = build_gt_events_from_validated(
                    validated,
                    num_blocks=len(original_payload_blocks),
                )
                pred_blocks = detect_sequence_multiple(
                    observed_sequence,
                    decoder_config=decoder_config,
                    codebook=codebook,
                )
                ev = evaluate_predictions_with_provenance(
                    original_payload_blocks=original_payload_blocks,
                    gt_events_per_block=gt_events_per_block,
                    pred_blocks=pred_blocks,
                    observed_provenance=edited_token_provenance,
                    tolerance=args.tolerance,
                    codebook=codebook,
                )
                edited_token_block_map = [
                    int(item["original_block_id"])
                    if item.get("original_block_id") is not None
                    else -1
                    for item in edited_token_provenance
                ]
                edited_token_bucket_ids = [int(x) for x in observed_sequence]
                edited_token_structural_symbols = [int(x) for x in observed_sequence]
                edited_token_structural_indices = list(range(len(observed_sequence)))
                edited_structural_sequence = [int(x) for x in observed_sequence]
                detector_block_details = build_detector_block_details(
                    pred_blocks=pred_blocks,
                    observed_sequence=observed_sequence,
                    tolerance=args.tolerance,
                    codebook=codebook,
                    boundary_symbol=codebook.boundary_symbol,
                )
                detector_aligned_block_text_spans, edited_token_block_map_from_detector = build_detector_aligned_block_text_spans(
                    edited_token_ids=edited_text_token_ids,
                    edited_token_structural_indices=edited_token_structural_indices,
                    detector_block_details=detector_block_details,
                    model=base_model,
                )
                edited_block_text_spans = build_block_text_spans(
                    edited_text_token_ids,
                    edited_token_block_map,
                    base_model,
                    num_blocks=len(original_payload_blocks),
                )
                edited_text = base_model.decode(edited_text_token_ids, skip_special_tokens=True)
                gt_blocks_flags = [int(len(events) > 0) for events in gt_events_per_block]
                pred_blocks_flags = [int(x) for x in ev["source_pred_flags"]]
                accepted_json = parsed_output
                accepted_instructions = validated
                used = True
                skip_reason = None
                summary_payload = {
                    "num_edited_blocks": int(sum(gt_blocks_flags)),
                    "block_edit_rate": float(sum(gt_blocks_flags) / max(1, len(gt_blocks_flags))),
                    "TP": int(ev["TP"]),
                    "FP": int(ev["FP"]),
                    "FN": int(ev["FN"]),
                    "TN": int(ev["TN"]),
                    "block_tpr": float(ev["block_tpr"]),
                    "block_far": float(ev["block_far"]),
                    "candidate_coverage": float(ev["event_coverage_overall"]),
                    "event_loc_hit": int(ev["event_loc_hit"]),
                    "event_total_overall": int(ev["event_total_overall"]),
                    "event_total_sub": int(ev["event_total_sub"]),
                    "event_total_insert": int(ev["event_total_insert"]),
                    "event_total_delete": int(ev["event_total_delete"]),
                    "pred_block_count": int(len(pred_blocks)),
                    "gt_block_count": int(len(gt_blocks_flags)),
                }
                break

            detail_rows.append(
                {
                    "sequence_index": sequence_index,
                    "motivation": motivation,
                    "intent_label": intent_label,
                    "used": used,
                    "skip_reason": skip_reason,
                    "reconstruction_mode": reconstruction_mode,
                    "reconstruction_exact_match": recon["exact_match"],
                    "reconstruction_match_rate": recon["match_rate"],
                    "num_edited_blocks": summary_payload.get("num_edited_blocks", 0),
                    "block_edit_rate": summary_payload.get("block_edit_rate", math.nan),
                    "accepted_edit_json": json.dumps(accepted_json, ensure_ascii=False) if accepted_json is not None else None,
                    "gt_blocks": json.dumps(gt_blocks_flags),
                    "pred_blocks": json.dumps(pred_blocks_flags),
                    "TP": summary_payload.get("TP", 0),
                    "FP": summary_payload.get("FP", 0),
                    "FN": summary_payload.get("FN", 0),
                    "TN": summary_payload.get("TN", 0),
                    "block_tpr": summary_payload.get("block_tpr", math.nan),
                    "block_far": summary_payload.get("block_far", math.nan),
                    "candidate_coverage": summary_payload.get("candidate_coverage", math.nan),
                    "event_loc_hit": summary_payload.get("event_loc_hit", 0),
                    "event_total_overall": summary_payload.get("event_total_overall", 0),
                    "original_text": suffix_text,
                    "edited_text": edited_text,
                    "original_token_ids_json": json.dumps(list(original_text_token_ids)),
                    "edited_token_ids_json": json.dumps(list(edited_text_token_ids)),
                    "original_token_block_map_json": json.dumps(list(original_token_block_map)),
                    "edited_token_block_map_json": json.dumps(list(edited_token_block_map)),
                    "edited_token_bucket_ids_json": json.dumps(list(edited_token_bucket_ids)),
                    "edited_token_structural_symbols_json": json.dumps(list(edited_token_structural_symbols)),
                    "edited_token_structural_index_json": json.dumps(list(edited_token_structural_indices)),
                    "edited_token_provenance_json": json.dumps(edited_token_provenance),
                    "edited_token_block_map_from_detector_json": json.dumps(list(edited_token_block_map_from_detector)),
                    "edited_structural_sequence_json": json.dumps(list(edited_structural_sequence)),
                    "pred_blocks_detailed_json": json.dumps(detector_block_details, ensure_ascii=False),
                    "parsed_to_source_blocks_json": json.dumps(ev.get("parsed_to_source_blocks", [])),
                    "source_candidate_locations_json": json.dumps(ev.get("source_candidate_locations", [])),
                    "detector_aligned_block_text_spans_json": json.dumps(detector_aligned_block_text_spans, ensure_ascii=False),
                    "original_block_text_spans_json": json.dumps(original_block_text_spans, ensure_ascii=False),
                    "edited_block_text_spans_json": json.dumps(edited_block_text_spans, ensure_ascii=False),
                }
            )
            instruction_records.append(
                {
                    "sequence_index": sequence_index,
                    "motivation": motivation,
                    "intent_label": intent_label,
                    "used": used,
                    "skip_reason": skip_reason,
                    "raw_output": last_raw_output,
                    "parsed_output": last_parsed_output,
                    "accepted_edit_json": accepted_json,
                    "validated_instructions": [
                        {
                            "op": item.op,
                            "original_index": item.original_index,
                            "gap_after": item.gap_after,
                            "original_text": item.original_text,
                            "new_content": item.new_content,
                            "reason": item.reason,
                            "tokenized_new_ids": item.tokenized_new_ids,
                            "mapped_new_buckets": item.mapped_new_buckets,
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
                        for item in accepted_instructions
                    ],
                    "reconstruction_info": {
                        "mode": reconstruction_mode,
                        "exact_match": recon["exact_match"],
                        "match_rate": recon["match_rate"],
                        "saved_bucket_len": len(saved_bucket_seq),
                        "retokenized_bucket_len": len(recon["retokenized_buckets"]),
                    },
                    "original_token_block_map": list(original_token_block_map),
                    "edited_token_block_map": list(edited_token_block_map),
                    "edited_token_bucket_ids": list(edited_token_bucket_ids),
                    "edited_token_structural_symbols": list(edited_token_structural_symbols),
                    "edited_token_structural_indices": list(edited_token_structural_indices),
                    "edited_token_block_map_from_detector": list(edited_token_block_map_from_detector),
                    "edited_structural_sequence": list(edited_structural_sequence),
                    "pred_blocks_detailed": detector_block_details,
                    "detector_aligned_block_text_spans": detector_aligned_block_text_spans,
                    "edited_block_text_spans": edited_block_text_spans,
                }
            )
            if args.checkpoint_every > 0 and len(detail_rows) % args.checkpoint_every == 0:
                write_checkpoint(
                    output_dir=args.output_dir,
                    detail_rows=detail_rows,
                    instruction_records=instruction_records,
                    total_expected_rows=total_expected_rows,
                )

    detail_df = pd.DataFrame(detail_rows)
    summary_df = build_summary_dataframe(detail_rows)
    save_dataframe(summary_df, str(Path(args.output_dir) / "llm_editor_summary"), save_parquet=True)
    save_dataframe(detail_df, str(Path(args.output_dir) / "llm_editor_details"), save_parquet=True)
    write_json(str(Path(args.output_dir) / "llm_edit_instructions.json"), instruction_records)
    write_json(
        str(Path(args.output_dir) / "llm_editor_config.json"),
        {
            "args": vars(args),
            "partition_prompt_file": partition_prompt_file,
            "partition_dir": args.partition_dir,
            "num_partition_texts": len(partition_texts),
            "partition_source": partition_source,
            "notes": {
                "authoritative_clean_structural_source": "saved generated_token_ids mapped through the loaded partition when available",
                "authoritative_edited_detector_source": "edited token ids mapped directly through the same partition; bucket-2 symbols are preserved",
                "retokenization_reconstruction": "diagnostic fallback only; exact generated token ids are preferred",
                "fallback_mode": "saved_bucket_sequence_fallback",
                "candidate_coverage_definition": "true edit location is covered if included in decoder returned candidate set",
                "parsed_block_pairing": "detector parsed spans are merged to fixed source blocks through token structural provenance",
            },
        },
    )
    return {
        "summary_df": summary_df,
        "detail_df": detail_df,
        "instruction_records": instruction_records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Independent sparse LLM-editor experiment for ECC watermark evaluation.")
    parser.add_argument("--seed-csv", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="outputs/llm_editor_delta20_sparse")
    parser.add_argument("--model-backend", type=str, choices=["mock", "hf"], default="mock")
    parser.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default=None)
    parser.add_argument("--model-name", type=str, default=None)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--partition-prompt-file", type=str, default=None)
    parser.add_argument("--partition-dir", type=str, default=None)
    parser.add_argument(
        "--require-semantic-partition",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--editor-backend", type=str, choices=["mock", "hf"], default="mock")
    parser.add_argument("--editor-model", type=str, default=None)
    parser.add_argument("--editor-enable-thinking", action="store_true")
    parser.add_argument("--editor-max-new-tokens", type=int, default=320)
    parser.add_argument("--question-aware", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-prompt-tokens", type=int, default=160)
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--checkpoint-every", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--resume-from-output-dir",
        type=str,
        default=None,
        help="Load prior details/instructions from another output directory.",
    )
    parser.add_argument(
        "--retry-skipped",
        action="store_true",
        help="With --resume, retain accepted rows and regenerate only skipped rows.",
    )
    parser.add_argument("--motivations", type=str, default="grammar_polish,clarity_improvement,style_softening,claim_distortion,stance_shift,source_spoofing")
    parser.add_argument("--motivation-assignment", choices=["all", "round_robin"], default="all")
    parser.add_argument("--max-edited-blocks", type=int, default=3)
    parser.add_argument("--min-edit-instructions", type=int, default=1)
    parser.add_argument("--max-edit-instructions", type=int, default=2)
    parser.add_argument("--max-block-edit-rate", type=float, default=0.5)
    parser.add_argument("--aggressive-malicious-edits", action="store_true")
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--decoder-max-edits-per-block", type=int, default=3)
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--tolerance", type=int, default=0)
    args = parser.parse_args()
    if args.retry_skipped and not args.resume:
        parser.error("--retry-skipped requires --resume.")
    if args.resume_from_output_dir and not args.resume:
        parser.error("--resume-from-output-dir requires --resume.")
    profile = get_model_profile(args.model_profile) if args.model_profile else None
    if profile and args.model_name and args.model_name != profile.model_name:
        parser.error(
            f"--model-profile {profile.key} requires --model-name {profile.model_name!r}."
        )
    args.model_name = args.model_name or (
        profile.model_name if profile else "Qwen/Qwen3-8B"
    )
    return args


def main() -> None:
    args = parse_args()
    result = run_editor_experiment(args)
    print("\nLLM editor summary:")
    print(result["summary_df"].to_string(index=False))


if __name__ == "__main__":
    main()
