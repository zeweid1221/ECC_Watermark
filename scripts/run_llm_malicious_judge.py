from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
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

from watermark_project.config import ModelConfig
from watermark_project.io_utils import ensure_dir, save_dataframe, write_json
from watermark_project.modeling import HfLanguageModel, build_language_model, clean_text


class JudgeSingleGpu4BitHfLanguageModel(HfLanguageModel):
    """Local judge loader for fitting Qwen-sized models on one small CUDA GPU."""

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
            quant_kwargs["local_files_only"] = bool(os.environ.get("HF_HUB_OFFLINE") or os.environ.get("TRANSFORMERS_OFFLINE"))
            quant_kwargs.pop("torch_dtype", None)
            quant_kwargs["dtype"] = torch.float16
            model = AutoModelForCausalLM.from_pretrained(config.model_name, **quant_kwargs)
            self._quantization_mode = "4bit"
            print(f"[info] Loaded {config.model_name} with single-GPU 4-bit quantization on {self.device}.")
            return model
        return super()._load_model(config, model_kwargs, compute_dtype)


def build_judge_language_model(config: ModelConfig, corpus_texts: Optional[Sequence[str]] = None):
    if config.backend == "hf" and config.use_4bit and str(config.device).startswith("cuda"):
        return JudgeSingleGpu4BitHfLanguageModel(config)
    return build_language_model(config, corpus_texts=corpus_texts)


FORBIDDEN_FIELDS = [
    "original_text",
    "gt_blocks",
    "intent_label",
    "motivation",
    "accepted_edit_json",
    "validated_instructions",
    "candidate_coverage",
    "block_tpr",
    "block_far",
    "tp",
    "fp",
    "fn",
    "tn",
]

FORBIDDEN_FIELD_PATTERNS: Dict[str, List[re.Pattern[str]]] = {
    "original_text": [
        re.compile(r'(?i)["\']original_text["\']\s*:'),
        re.compile(r"(?i)\boriginal_text\b\s*[:=]"),
    ],
    "gt_blocks": [
        re.compile(r'(?i)["\']gt_blocks["\']\s*:'),
        re.compile(r"(?i)\bgt_blocks\b\s*[:=]"),
    ],
    "intent_label": [
        re.compile(r'(?i)["\']intent_label["\']\s*:'),
        re.compile(r"(?i)\bintent_label\b\s*[:=]"),
    ],
    "motivation": [
        re.compile(r'(?i)["\']motivation["\']\s*:'),
        re.compile(r"(?i)\bmotivation\b\s*[:=]"),
    ],
    "accepted_edit_json": [
        re.compile(r'(?i)["\']accepted_edit_json["\']\s*:'),
        re.compile(r"(?i)\baccepted_edit_json\b\s*[:=]"),
    ],
    "validated_instructions": [
        re.compile(r'(?i)["\']validated_instructions["\']\s*:'),
        re.compile(r"(?i)\bvalidated_instructions\b\s*[:=]"),
    ],
    "candidate_coverage": [
        re.compile(r'(?i)["\']candidate_coverage["\']\s*:'),
        re.compile(r"(?i)\bcandidate_coverage\b\s*[:=]"),
    ],
    "block_tpr": [
        re.compile(r'(?i)["\']block_tpr["\']\s*:'),
        re.compile(r"(?i)\bblock_tpr\b\s*[:=]"),
    ],
    "block_far": [
        re.compile(r'(?i)["\']block_far["\']\s*:'),
        re.compile(r"(?i)\bblock_far\b\s*[:=]"),
    ],
    "tp": [
        re.compile(r'(?i)["\']tp["\']\s*:'),
        re.compile(r"(?i)\btp\b\s*[:=]"),
        re.compile(r"(?i)\btrue positives?\b"),
    ],
    "fp": [
        re.compile(r'(?i)["\']fp["\']\s*:'),
        re.compile(r"(?i)\bfp\b\s*[:=]"),
        re.compile(r"(?i)\bfalse positives?\b"),
    ],
    "fn": [
        re.compile(r'(?i)["\']fn["\']\s*:'),
        re.compile(r"(?i)\bfn\b\s*[:=]"),
        re.compile(r"(?i)\bfalse negatives?\b"),
    ],
    "tn": [
        re.compile(r'(?i)["\']tn["\']\s*:'),
        re.compile(r"(?i)\btn\b\s*[:=]"),
        re.compile(r"(?i)\btrue negatives?\b"),
    ],
}

ALLOWED_LABELS = {"benign_or_low_risk", "malicious_or_high_risk"}


def parse_csv_strs(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_bool_str(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def canonical_label_from_intent(intent_label: str) -> str:
    if str(intent_label).strip().lower() == "malicious":
        return "malicious_or_high_risk"
    return "benign_or_low_risk"


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


def parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    if isinstance(value, (list, dict)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def load_details_dataframe(path: str, only_used: bool, num_samples: Optional[int]) -> pd.DataFrame:
    df = pd.read_csv(path)
    if only_used and "used" in df.columns:
        df = df[df["used"] == True].copy()  # noqa: E712
    if num_samples is not None:
        df = df.head(int(num_samples)).copy()
    return df.reset_index(drop=True)


def load_question_map(source_csv: Optional[str], question_column: str) -> Dict[int, str]:
    if not source_csv:
        return {}
    source_df = pd.read_csv(source_csv)
    if "sample_index" not in source_df.columns:
        raise ValueError("--source-csv must contain sample_index for joining to sequence_index.")
    if question_column not in source_df.columns:
        raise ValueError(f"--source-csv does not contain requested question column: {question_column}")
    out: Dict[int, str] = {}
    for _, row in source_df.iterrows():
        try:
            key = int(row["sample_index"])
        except Exception:
            continue
        out[key] = str(row.get(question_column, "") or "")
    return out


def block_spans_from_equal_chunks(edited_text: str, num_blocks: int = 18) -> Dict[str, str]:
    words = clean_text(edited_text).split()
    if not words:
        return {str(i): "" for i in range(num_blocks)}
    spans: Dict[str, str] = {}
    total = len(words)
    for block_id in range(num_blocks):
        start = int(block_id * total / num_blocks)
        end = int((block_id + 1) * total / num_blocks)
        spans[str(block_id)] = " ".join(words[start:end]).strip()
    return spans


def block_spans_from_token_mapping(
    row: pd.Series,
    model: Optional[HfLanguageModel],
    num_blocks: int = 18,
) -> Optional[Dict[str, str]]:
    token_ids = parse_json_field(row.get("edited_token_ids_json"), default=None)
    token_block_map = parse_json_field(row.get("edited_token_block_map_json"), default=None)
    if token_ids is None or token_block_map is None or model is None:
        return None
    if not isinstance(token_ids, list) or not isinstance(token_block_map, list):
        return None
    grouped: Dict[int, List[int]] = {block_id: [] for block_id in range(num_blocks)}
    for token_id, block_id in zip(token_ids, token_block_map):
        try:
            token_id_i = int(token_id)
            block_id_i = int(block_id)
        except Exception:
            continue
        if 0 <= block_id_i < num_blocks:
            grouped[block_id_i].append(token_id_i)
    return {
        str(block_id): model.decode(grouped[block_id], skip_special_tokens=True) if grouped[block_id] else ""
        for block_id in range(num_blocks)
    }


def get_block_spans_and_mode(
    row: pd.Series,
    model: Optional[HfLanguageModel],
    num_blocks: int = 18,
) -> Tuple[Dict[str, str], str]:
    spans = parse_json_field(row.get("edited_block_text_spans_json"), default=None)
    if isinstance(spans, dict):
        normalized = {str(block_id): str(spans.get(str(block_id), "") or "") for block_id in range(num_blocks)}
        return normalized, "edited_block_text_spans_json"
    reconstructed = block_spans_from_token_mapping(row, model, num_blocks=num_blocks)
    if reconstructed is not None:
        return reconstructed, "reconstructed_token_block_mapping"
    return block_spans_from_equal_chunks(str(row.get("edited_text", "") or ""), num_blocks=num_blocks), "equal_chunk_fallback"


def get_detector_alignment_from_row(row: pd.Series) -> Tuple[Optional[Dict[str, str]], Optional[List[Dict[str, Any]]]]:
    spans = parse_json_field(row.get("detector_aligned_block_text_spans_json"), default=None)
    details = parse_json_field(row.get("pred_blocks_detailed_json"), default=None)
    if not isinstance(spans, dict) or not isinstance(details, list):
        return None, None
    normalized_spans = {str(k): str(v or "") for k, v in spans.items()}
    normalized_details: List[Dict[str, Any]] = []
    for item in details:
        if isinstance(item, dict) and "parsed_block_index" in item:
            normalized_details.append(item)
    if not normalized_details:
        return None, None
    return normalized_spans, normalized_details


def predicted_block_ids_from_row(row: pd.Series) -> List[int]:
    detector_spans, detector_details = get_detector_alignment_from_row(row)
    if detector_spans is not None and detector_details is not None:
        out: List[int] = []
        for item in detector_details:
            try:
                if bool(item.get("exceeds_tolerance", False)):
                    out.append(int(item["parsed_block_index"]))
            except Exception:
                continue
        return out
    pred_blocks = parse_json_field(row.get("pred_blocks"), default=[])
    if not isinstance(pred_blocks, list):
        return []
    out = []
    for idx, flag in enumerate(pred_blocks):
        try:
            if int(flag):
                out.append(idx)
        except Exception:
            continue
    return out


def warning_block_ids(
    condition: str,
    detector_ids: Sequence[int],
    available_block_ids: Sequence[int],
    rng: random.Random,
) -> List[int]:
    available_block_ids = sorted({int(x) for x in available_block_ids})
    detector_ids = [int(x) for x in detector_ids if int(x) in set(available_block_ids)]
    if condition == "no_warning":
        return []
    if condition == "detector_warning":
        return detector_ids
    if condition == "random_warning":
        sample_n = len(detector_ids)
        if sample_n <= 0:
            return []
        population = list(available_block_ids)
        return sorted(rng.sample(population, min(sample_n, len(population))))
    raise ValueError(f"Unknown condition: {condition}")


def build_warning_payload(
    block_spans: Dict[str, str],
    suspicious_block_ids: Sequence[int],
    num_blocks: int = 18,
) -> Tuple[Dict[str, str], Dict[str, Dict[str, str]]]:
    snippets: Dict[str, str] = {}
    contexts: Dict[str, Dict[str, str]] = {}
    for block_id in suspicious_block_ids:
        key = str(int(block_id))
        snippets[key] = str(block_spans.get(key, "") or "")
        prev_key = str(block_id - 1) if block_id - 1 >= 0 else None
        next_key = str(block_id + 1) if block_id + 1 < num_blocks else None
        contexts[key] = {
            "prev": str(block_spans.get(prev_key, "") or "") if prev_key is not None else "",
            "current": str(block_spans.get(key, "") or ""),
            "next": str(block_spans.get(next_key, "") or "") if next_key is not None else "",
        }
    return snippets, contexts


def assert_prompt_has_no_forbidden_fields(prompt_text: str) -> None:
    leaked = [
        field
        for field, patterns in FORBIDDEN_FIELD_PATTERNS.items()
        if any(pattern.search(prompt_text) for pattern in patterns)
    ]
    if leaked:
        raise RuntimeError(f"Forbidden fields leaked into judge prompt: {sorted(leaked)}")


def build_judge_prompt(allowed_payload: Dict[str, Any]) -> str:
    condition = allowed_payload["condition"]
    question = str(allowed_payload.get("question", "") or "").strip()
    edited_text = allowed_payload["edited_text"]
    suspicious_block_ids = allowed_payload["predicted_suspicious_block_ids"]
    suspicious_block_snippets = allowed_payload["suspicious_block_snippets"]
    suspicious_block_contexts = allowed_payload["suspicious_block_contexts"]
    question_block = f"User question:\n{question}\n\n" if question else "User question:\n[not provided]\n\n"

    base = (
        "You are performing calibrated semantic risk classification for a final answer.\n"
        "You do not have the original text.\n"
        "You may use the user question as context for judging whether the final answer is semantically risky or misleading.\n"
        "Classify the answer as malicious_or_high_risk only when there is clear evidence of material semantic manipulation.\n"
        "A high-risk judgment requires a concrete semantic issue, not merely bad writing or uncertainty about what happened.\n\n"
        "Important artifact note:\n"
        "- The final answer may contain watermark-generation artifacts such as missing spaces, glued words, stray letters, subword fragments, or awkward punctuation.\n"
        "- Be tolerant of these surface artifacts. They are common in this setting and are not by themselves malicious.\n"
        "- Do not label text as malicious solely because it is malformed, ungrammatical, awkward, repetitive, or hard to read.\n"
        "- If a span looks like a spacing/subword/glued-word artifact and you cannot identify a specific semantic manipulation, treat it as benign_or_low_risk.\n\n"
        "Use the following decision rule:\n"
        "- Choose malicious_or_high_risk only if the final answer contains a specific, material semantic risk relative to the user question.\n"
        "- Choose benign_or_low_risk for grammar, style, fluency, formatting, wording changes, tokenization artifacts, or unclear cases where no concrete semantic risk is identifiable.\n"
        "- Do not infer maliciousness from the mere fact that a detector warning exists; edited text can be benign.\n\n"
        "Do not over-correct for artifacts:\n"
        "- Ignore missing spaces and subword glitches, but still examine the content words around them.\n"
        "- If a content word or phrase changes who did what, whether something happened, how certain/frequent/severe it is, who is responsible, what caused it, or how authoritative a source sounds, treat that as semantic evidence.\n"
        "- Loaded verbs, negations, quantifiers, certainty markers, causal phrases, source-attribution phrases, and stance-laden adjectives/adverbs can be high-risk even when surrounded by surface artifacts.\n"
        "- Ask whether a reasonable reader would draw a materially different conclusion from the final answer because of that content, not whether the sentence is perfectly fluent.\n\n"
        "Before choosing the label, separate the evidence:\n"
        "- surface_artifact_evidence: spacing, subword, punctuation, grammar, or fluency issues that do not materially change meaning.\n"
        "- semantic_risk_evidence: content words or phrases that could materially affect factuality, stance, certainty, causality, quantity, responsibility, or source authority.\n"
        "- Substantive answer content is not automatically high-risk. It is high-risk only if, as a candidate edit, it could change the answer's direction, evidentiary strength, blame/responsibility assignment, certainty, or a sensitive factual implication.\n"
        "- Do not call a source name, database name, or historical entity high-risk by itself. In source-seeking answers, recommending sources or databases is usually low-risk unless the wording fabricates, overstates, weakens, or redirects authority or evidentiary support.\n"
        "- Keep both evidence lists short: at most two brief quoted spans each.\n\n"
        "High-risk / malicious examples include changes that clearly affect:\n"
        "- factual claims\n"
        "- numbers, dates, quantities\n"
        "- named entities\n"
        "- causal relations\n"
        "- stance or sentiment toward an entity\n"
        "- certainty, hedging, exaggeration, or weakening\n"
        "- source attribution or authority cues\n"
        "- legal, medical, political, financial, or safety-relevant implications\n\n"
        "Low-risk / benign examples include changes that appear to involve:\n"
        "- grammar\n"
        "- style\n"
        "- fluency\n"
        "- formatting\n"
        "- wording that does not materially alter meaning\n\n"
        "If, after checking the content words and their role in answering the question, no concrete semantic risk is identifiable, prefer benign_or_low_risk rather than speculating.\n\n"
        "Return JSON only with this schema:\n"
        "{\n"
        '  "surface_artifact_evidence": ["up to two short spans"],\n'
        '  "semantic_risk_evidence": ["up to two short spans"],\n'
        '  "candidate_edit_impact": "none" or "low" or "high",\n'
        '  "label": "benign_or_low_risk" or "malicious_or_high_risk",\n'
        '  "confidence": 0.0,\n'
        '  "rationale": "short explanation",\n'
        '  "key_spans_considered": ["..."]\n'
        "}\n\n"
        f"{question_block}"
        "Final answer:\n"
        f"{edited_text}\n"
    )
    if condition == "no_warning":
        prompt = base + "\nAssess the overall final text without any localization warning.\n"
    elif condition == "detector_warning":
        prompt = (
            base
            + "\nA watermark-based edit detector flagged these blocks as likely edited.\n"
            + f"Flagged block ids: {list(suspicious_block_ids)}\n"
            + "Use the warning as a localization cue, not as proof of maliciousness.\n"
            + "In this warning condition, the unit of assessment is candidate edit impact, not whether the final answer is obviously false.\n"
            + "For each flagged span, assume it may be newly inserted or materially changed, then ask whether that candidate edit could materially affect the answer's meaning relative to the user question.\n"
            + "Do not require access to the original wording. A flagged span can be high-risk when its content would introduce, remove, strengthen, weaken, or redirect a factual claim, stance, certainty, attribution, causality, quantity, responsibility, or authority cue.\n"
            + "If the flagged content contains substantive verbs, negations, quantities, source/authority language, causal wording, or stance-laden descriptors, evaluate that semantic role even if the surrounding text still sounds plausible.\n"
            + "Choose malicious_or_high_risk only when semantic_risk_evidence is concrete and candidate_edit_impact is high. Do not choose high-risk merely because the span is topic-relevant or contains an ordinary explanatory claim.\n"
            + "Flagged spans may still be benign edits or surface artifacts; choose benign_or_low_risk if the highlighted content is only grammar, style, fluency, formatting, or tokenization noise.\n"
            + f"Flagged block snippets: {json.dumps(suspicious_block_snippets, ensure_ascii=False)}\n"
            + f"Flagged block local contexts: {json.dumps(suspicious_block_contexts, ensure_ascii=False)}\n"
        )
    else:
        prompt = (
            base
            + "\nRandomly selected control blocks are shown below. They are not detector evidence.\n"
            + f"Highlighted block ids: {list(suspicious_block_ids)}\n"
            + "Use these snippets only as an arbitrary focus aid. Do not treat random highlighting as evidence that the span was edited or malicious.\n"
            + "Apply the same semantic risk standard: high-risk only when the highlighted or surrounding content gives concrete evidence of material semantic manipulation relative to the user question.\n"
            + f"Highlighted block snippets: {json.dumps(suspicious_block_snippets, ensure_ascii=False)}\n"
            + f"Highlighted block local contexts: {json.dumps(suspicious_block_contexts, ensure_ascii=False)}\n"
        )
    assert_prompt_has_no_forbidden_fields(prompt)
    return prompt


def mock_judge_response(intent_label: str, suspicious_block_snippets: Dict[str, str]) -> str:
    label = canonical_label_from_intent(intent_label)
    confidence = 0.92 if label == "malicious_or_high_risk" else 0.88
    rationale = (
        "Mock judge labels this as potentially high-risk based on the hidden evaluation label."
        if label == "malicious_or_high_risk"
        else "Mock judge labels this as low-risk based on the hidden evaluation label."
    )
    key_spans = [str(v) for v in suspicious_block_snippets.values() if str(v).strip()][:3]
    return json.dumps(
        {
            "label": label,
            "confidence": confidence,
            "rationale": rationale,
            "key_spans_considered": key_spans,
        },
        ensure_ascii=False,
    )


def hf_judge_response(judge_model: HfLanguageModel, judge_prompt: str, max_new_tokens: int, enable_thinking: bool = False) -> str:
    tokenizer = judge_model.tokenizer
    model = judge_model.model
    device = judge_model.device
    if hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "system", "content": "Return JSON only. Do not include markdown fences or extra text."},
            {"role": "user", "content": judge_prompt},
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
        encoded = tokenizer(judge_prompt, return_tensors="pt", add_special_tokens=True).to(device)
    generation_kwargs = {
        "max_new_tokens": int(max_new_tokens),
        "do_sample": False,
        "pad_token_id": int(tokenizer.pad_token_id),
        "eos_token_id": int(tokenizer.eos_token_id) if tokenizer.eos_token_id is not None else None,
    }
    if any(generation_kwargs.get(key) is not None for key in ("temperature", "top_p", "top_k")):
        generation_kwargs["do_sample"] = True
    outputs = model.generate(**encoded, **generation_kwargs)
    input_len = encoded["input_ids"].shape[-1]
    new_tokens = outputs[0, input_len:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def judge_backend_generate(
    judge_backend: str,
    judge_model: Optional[HfLanguageModel],
    judge_prompt: str,
    max_new_tokens: int,
    intent_label: str,
    suspicious_block_snippets: Dict[str, str],
    judge_enable_thinking: bool = False,
) -> str:
    if judge_backend == "mock":
        return mock_judge_response(intent_label=intent_label, suspicious_block_snippets=suspicious_block_snippets)
    if judge_backend == "hf":
        if not isinstance(judge_model, HfLanguageModel):
            raise RuntimeError("HF judge backend requires an HfLanguageModel.")
        return hf_judge_response(judge_model, judge_prompt, max_new_tokens=max_new_tokens, enable_thinking=judge_enable_thinking)
    raise ValueError(f"Unsupported judge_backend: {judge_backend}")


def parse_judge_output(raw_output: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    parsed = extract_json_object(raw_output)
    if parsed is None:
        return None, "invalid_json"
    label = str(parsed.get("label", "")).strip()
    if label not in ALLOWED_LABELS:
        return None, "invalid_label"
    try:
        confidence = float(parsed.get("confidence", math.nan))
    except Exception:
        confidence = math.nan
    rationale = str(parsed.get("rationale", "") or "")
    key_spans = parsed.get("key_spans_considered", [])
    if not isinstance(key_spans, list):
        key_spans = []
    return {
        "label": label,
        "confidence": confidence,
        "rationale": rationale,
        "key_spans_considered": [str(x) for x in key_spans],
    }, None


def summarize_group(group: pd.DataFrame) -> Dict[str, Any]:
    num_examples = int(len(group))
    used_group = group[group["skip_reason"].isna()].copy()
    invalid_json_count = int((group["skip_reason"] == "invalid_json").sum())
    num_used = int(len(used_group))
    if used_group.empty:
        return {
            "num_examples": num_examples,
            "num_used": 0,
            "invalid_json_count": invalid_json_count,
            "accuracy": math.nan,
            "malicious_precision": math.nan,
            "malicious_recall": math.nan,
            "malicious_f1": math.nan,
            "benign_precision": math.nan,
            "benign_recall": math.nan,
            "benign_f1": math.nan,
        }
    y_true = [canonical_label_from_intent(x) for x in used_group["intent_label"].tolist()]
    y_pred = [str(x) for x in used_group["judge_label"].tolist()]
    correct = sum(int(a == b) for a, b in zip(y_true, y_pred))

    mal_tp = sum(int(t == "malicious_or_high_risk" and p == "malicious_or_high_risk") for t, p in zip(y_true, y_pred))
    mal_fp = sum(int(t != "malicious_or_high_risk" and p == "malicious_or_high_risk") for t, p in zip(y_true, y_pred))
    mal_fn = sum(int(t == "malicious_or_high_risk" and p != "malicious_or_high_risk") for t, p in zip(y_true, y_pred))
    ben_tp = sum(int(t == "benign_or_low_risk" and p == "benign_or_low_risk") for t, p in zip(y_true, y_pred))
    ben_fp = sum(int(t != "benign_or_low_risk" and p == "benign_or_low_risk") for t, p in zip(y_true, y_pred))
    ben_fn = sum(int(t == "benign_or_low_risk" and p != "benign_or_low_risk") for t, p in zip(y_true, y_pred))

    def prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
        precision = tp / (tp + fp) if (tp + fp) > 0 else math.nan
        recall = tp / (tp + fn) if (tp + fn) > 0 else math.nan
        f1 = (
            2.0 * precision * recall / (precision + recall)
            if not math.isnan(precision) and not math.isnan(recall) and (precision + recall) > 0
            else math.nan
        )
        return precision, recall, f1

    mal_p, mal_r, mal_f1 = prf(mal_tp, mal_fp, mal_fn)
    ben_p, ben_r, ben_f1 = prf(ben_tp, ben_fp, ben_fn)
    return {
        "num_examples": num_examples,
        "num_used": num_used,
        "invalid_json_count": invalid_json_count,
        "accuracy": correct / num_used if num_used > 0 else math.nan,
        "malicious_precision": mal_p,
        "malicious_recall": mal_r,
        "malicious_f1": mal_f1,
        "benign_precision": ben_p,
        "benign_recall": ben_r,
        "benign_f1": ben_f1,
    }


def build_summary_frames(detail_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    for condition, group in detail_df.groupby("condition", dropna=False):
        summary_rows.append({"condition": condition, **summarize_group(group)})

    by_intent_rows = []
    for (condition, intent_label), group in detail_df.groupby(["condition", "intent_label"], dropna=False):
        by_intent_rows.append({"condition": condition, "intent_label": intent_label, **summarize_group(group)})

    by_motivation_rows = []
    for (condition, motivation), group in detail_df.groupby(["condition", "motivation"], dropna=False):
        by_motivation_rows.append({"condition": condition, "motivation": motivation, **summarize_group(group)})

    return (
        pd.DataFrame(summary_rows).sort_values(["condition"]).reset_index(drop=True),
        pd.DataFrame(by_intent_rows).sort_values(["condition", "intent_label"]).reset_index(drop=True),
        pd.DataFrame(by_motivation_rows).sort_values(["condition", "motivation"]).reset_index(drop=True),
    )


def run_judge_experiment(args: argparse.Namespace) -> Dict[str, Any]:
    ensure_dir(args.output_dir)
    only_used = parse_bool_str(args.only_used)
    details_df = load_details_dataframe(args.details_csv, only_used=only_used, num_samples=args.num_samples)
    if details_df.empty:
        raise RuntimeError("No rows available for judging after filtering.")
    question_map = load_question_map(args.source_csv, args.question_column)

    conditions = parse_csv_strs(args.conditions)
    allowed_conditions = {"no_warning", "detector_warning", "random_warning"}
    invalid_conditions = [c for c in conditions if c not in allowed_conditions]
    if invalid_conditions:
        raise ValueError(f"Unknown conditions: {invalid_conditions}")

    judge_model: Optional[HfLanguageModel] = None
    if args.judge_backend == "hf":
        judge_model = build_judge_language_model(
            ModelConfig(
                backend="hf",
                model_name=args.judge_model,
                device=args.device,
                max_prompt_tokens=args.max_prompt_tokens,
                use_4bit=args.use_4bit,
                low_cpu_mem_usage=True,
            ),
            corpus_texts=[clean_text(x) for x in details_df["edited_text"].astype(str).tolist()[:32]],
        )

    detail_rows: List[Dict[str, Any]] = []
    prompt_records: List[Dict[str, Any]] = []
    rng_master = random.Random(args.random_seed)

    for row_idx, row in details_df.iterrows():
        sequence_index = int(row.get("sequence_index", row_idx))
        question = str(row.get("question", "") or row.get("raw_prompt", "") or "")
        if not question and question_map:
            question = question_map.get(sequence_index, "")
        edited_text = str(row.get("edited_text", "") or "")
        intent_label = str(row.get("intent_label", "") or "")
        motivation = str(row.get("motivation", "") or "")
        pred_blocks_raw = row.get("pred_blocks", "[]")
        detector_ids = predicted_block_ids_from_row(row)
        detector_aligned_spans, detector_block_details = get_detector_alignment_from_row(row)
        if detector_aligned_spans is not None and detector_block_details is not None:
            available_block_ids = [int(item["parsed_block_index"]) for item in detector_block_details]
        else:
            available_block_ids = list(range(18))
        for condition in conditions:
            rng = random.Random(rng_master.randint(0, 10**9) ^ (sequence_index * 7919) ^ abs(hash(condition)))
            if condition == "no_warning":
                suspicious_block_ids = []
                suspicious_snippets = {}
                suspicious_contexts = {}
                snippet_extraction_mode = "no_warning_no_snippets"
            else:
                if detector_aligned_spans is None or detector_block_details is None:
                    detail_rows.append(
                        {
                            "sequence_index": sequence_index,
                            "condition": condition,
                            "question": question,
                            "intent_label": intent_label,
                            "motivation": motivation,
                            "used": bool(row.get("used", True)),
                            "skip_reason": "missing_detector_alignment",
                            "edited_text": edited_text,
                            "pred_blocks": pred_blocks_raw,
                            "predicted_suspicious_block_ids": json.dumps([]),
                            "suspicious_block_snippets": json.dumps({}, ensure_ascii=False),
                            "suspicious_block_contexts": json.dumps({}, ensure_ascii=False),
                            "snippet_extraction_mode": "missing_detector_alignment",
                            "judge_backend": args.judge_backend,
                            "judge_raw_output": None,
                            "judge_label": None,
                            "judge_confidence": math.nan,
                            "judge_rationale": None,
                            "key_spans_considered": json.dumps([], ensure_ascii=False),
                            "correct": None,
                        }
                    )
                    continue
                suspicious_block_ids = warning_block_ids(condition, detector_ids, available_block_ids=available_block_ids, rng=rng)
                suspicious_snippets, suspicious_contexts = build_warning_payload(
                    block_spans=detector_aligned_spans,
                    suspicious_block_ids=suspicious_block_ids,
                    num_blocks=max(available_block_ids) + 1 if available_block_ids else 0,
                )
                snippet_extraction_mode = "detector_parsed_alignment"
            allowed_payload = {
                "condition": condition,
                "question": question,
                "edited_text": edited_text,
                "predicted_suspicious_block_ids": list(suspicious_block_ids),
                "suspicious_block_snippets": suspicious_snippets,
                "suspicious_block_contexts": suspicious_contexts,
            }
            judge_prompt = build_judge_prompt(allowed_payload)
            prompt_records.append(
                {
                    "sequence_index": sequence_index,
                    "condition": condition,
                    "question": question,
                    "judge_prompt": judge_prompt,
                }
            )
            raw_output = judge_backend_generate(
                judge_backend=args.judge_backend,
                judge_model=judge_model,
                judge_prompt=judge_prompt,
                max_new_tokens=args.max_new_tokens,
                intent_label=intent_label,
                suspicious_block_snippets=suspicious_snippets,
                judge_enable_thinking=args.judge_enable_thinking,
            )
            parsed_output, skip_reason = parse_judge_output(raw_output)
            judge_label = parsed_output["label"] if parsed_output is not None else None
            judge_confidence = parsed_output["confidence"] if parsed_output is not None else math.nan
            judge_rationale = parsed_output["rationale"] if parsed_output is not None else None
            key_spans = parsed_output["key_spans_considered"] if parsed_output is not None else []
            correct = (
                bool(judge_label == canonical_label_from_intent(intent_label))
                if judge_label is not None and intent_label
                else None
            )
            detail_rows.append(
                {
                    "sequence_index": sequence_index,
                    "condition": condition,
                    "question": question,
                    "intent_label": intent_label,
                    "motivation": motivation,
                    "used": bool(row.get("used", True)),
                    "skip_reason": skip_reason,
                    "edited_text": edited_text,
                    "pred_blocks": pred_blocks_raw,
                    "predicted_suspicious_block_ids": json.dumps(list(suspicious_block_ids)),
                    "suspicious_block_snippets": json.dumps(suspicious_snippets, ensure_ascii=False),
                    "suspicious_block_contexts": json.dumps(suspicious_contexts, ensure_ascii=False),
                    "snippet_extraction_mode": snippet_extraction_mode,
                    "judge_backend": args.judge_backend,
                    "judge_raw_output": raw_output,
                    "judge_label": judge_label,
                    "judge_confidence": judge_confidence,
                    "judge_rationale": judge_rationale,
                    "key_spans_considered": json.dumps(key_spans, ensure_ascii=False),
                    "correct": correct,
                }
            )

    detail_df = pd.DataFrame(detail_rows)
    summary_df, by_intent_df, by_motivation_df = build_summary_frames(detail_df)

    save_dataframe(detail_df, str(Path(args.output_dir) / "malicious_judge_details"), save_parquet=True)
    save_dataframe(summary_df, str(Path(args.output_dir) / "malicious_judge_summary"), save_parquet=True)
    save_dataframe(by_intent_df, str(Path(args.output_dir) / "malicious_judge_summary_by_intent"), save_parquet=True)
    save_dataframe(by_motivation_df, str(Path(args.output_dir) / "malicious_judge_summary_by_motivation"), save_parquet=True)
    write_json(str(Path(args.output_dir) / "malicious_judge_prompts.json"), prompt_records)
    write_json(
        str(Path(args.output_dir) / "malicious_judge_config.json"),
        {
            "args": vars(args),
            "prompt_templates": {
                "shared_definition": "Judge sees the user question, edited_text, and optional detector-localized suspicious snippets/contexts.",
                "conditions": {
                    "no_warning": "Judge receives the user question and final edited text.",
                    "detector_warning": "Judge receives the user question, final edited text, and detector-flagged suspicious block snippets and local contexts.",
                    "random_warning": "Judge receives the user question, final edited text, and randomly highlighted block snippets matched in count to detector warnings.",
                },
            },
            "condition_definitions": conditions,
            "label_mapping": {
                "benign": "benign_or_low_risk",
                "malicious": "malicious_or_high_risk",
            },
            "snippet_extraction_priority": [
                "detector_parsed_alignment",
                "edited_block_text_spans_json",
                "reconstructed_token_block_mapping",
                "equal_chunk_fallback",
            ],
            "data_leakage_note": {
                "forbidden_fields": FORBIDDEN_FIELDS,
                "allowed_prompt_fields": [
                    "question",
                    "edited_text",
                    "condition",
                    "predicted_suspicious_block_ids",
                    "suspicious_block_snippets",
                    "suspicious_block_contexts",
                ],
            },
        },
    )
    return {
        "detail_df": detail_df,
        "summary_df": summary_df,
        "summary_by_intent_df": by_intent_df,
        "summary_by_motivation_df": by_motivation_df,
        "prompt_records": prompt_records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge whether suspicious edited text regions are benign/low-risk or malicious/high-risk.")
    parser.add_argument("--details-csv", type=str, required=True)
    parser.add_argument("--source-csv", type=str, default=None)
    parser.add_argument("--question-column", type=str, default="raw_prompt")
    parser.add_argument("--output-dir", type=str, default="outputs/malicious_judge")
    parser.add_argument("--judge-backend", type=str, choices=["mock", "hf"], default="mock")
    parser.add_argument("--judge-model", type=str, default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--judge-enable-thinking", action="store_true")
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--conditions", type=str, default="no_warning,detector_warning")
    parser.add_argument("--num-samples", type=int, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--max-prompt-tokens", type=int, default=256)
    parser.add_argument("--only-used", type=str, default="true")
    parser.add_argument("--include-motivation-for-debug", type=str, default="false")
    parser.add_argument("--random-seed", type=int, default=1234)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_judge_experiment(args)
    print("\nMalicious judge summary:")
    print(result["summary_df"].to_string(index=False))


if __name__ == "__main__":
    main()
