from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from transformers import AutoTokenizer

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.preview_watermarked_generation_quality import load_prompt_lines  # noqa: E402
from watermark_project.config import ECCConfig  # noqa: E402
from watermark_project.modeling import clean_text  # noqa: E402
from watermark_project.partitioning import (  # noqa: E402
    build_token_frequency,
    build_vocabulary_partition_from_boundary_ids,
    normalize_surface,
    save_vocabulary_partition,
)


DEFAULT_CANDIDATE_FILE = PROJECT_ROOT / "resources" / "boundary_candidates_qwen3_v1.txt"

FORBIDDEN_BOUNDARY_SURFACES = {
    "a", "an", "the",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our", "its",
    "this", "that", "these", "those",
    "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "of", "to", "in", "on", "at", "by", "for", "from", "with", "as", "or", "and", "but",
    "if", "then", "than", "so", "not", "no", "yes",
    "can", "may", "might", "must", "should", "would", "could", "will",
    # Common words that were visibly bad boundary choices in earlier artifacts.
    "often", "common", "part", "direct", "able", "over", "under",
}

SURFACE_RE = re.compile(r"^[A-Za-z][A-Za-z-]{2,}$")


class TokenizerOnlyLanguageModel:
    """Minimal tokenizer adapter for partition construction.

    Bucket construction only needs encode/decode, vocab size, and special-token
    ids. Loading full causal-LM weights here is unnecessary and brittle on a
    local 8GB GPU.
    """

    def __init__(self, model_name: str) -> None:
        local_only = False
        import os

        if os.environ.get("HF_HUB_OFFLINE") or os.environ.get("TRANSFORMERS_OFFLINE"):
            local_only = True
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, local_files_only=local_only)
        self.vocab_size = len(self.tokenizer)
        self.all_special_ids = [int(x) for x in self.tokenizer.all_special_ids]

    def encode(self, text: str, add_special_tokens: bool = False) -> List[int]:
        return [int(x) for x in self.tokenizer.encode(text, add_special_tokens=add_special_tokens)]

    def decode(self, token_ids: Sequence[int], skip_special_tokens: bool = True) -> str:
        return self.tokenizer.decode([int(x) for x in token_ids], skip_special_tokens=skip_special_tokens)

    def token_surface(self, token_id: int) -> str:
        return self.decode([int(token_id)], skip_special_tokens=False)

    def embedding_matrix(self) -> None:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fixed Qwen3 ECC vocabulary partition artifact.")
    parser.add_argument("--model-name", default="Qwen/Qwen3-8B")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--candidate-file", default=str(DEFAULT_CANDIDATE_FILE))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--target-boundary-size", type=int, default=150)
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--max-prompt-tokens", type=int, default=256)
    parser.add_argument("--max-boundary-frequency", type=int, default=50)
    parser.add_argument("--min-surface-len", type=int, default=3)
    return parser.parse_args()


def load_candidate_words(path: str | Path) -> List[str]:
    out: List[str] = []
    seen = set()
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            key = line.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(line)
    return out


def word_to_single_token_id(model: Any, word: str) -> Tuple[Optional[int], str]:
    tokenizer = getattr(model, "tokenizer", None)

    def encode_candidate(text: str) -> List[int]:
        # Leading whitespace is semantically significant for BPE tokenizers.
        # The generation adapter cleans ordinary input text, so use the raw
        # tokenizer here instead of model.encode() when it is available.
        if tokenizer is not None:
            return [
                int(token_id)
                for token_id in tokenizer.encode(text, add_special_tokens=False)
            ]
        return [
            int(token_id)
            for token_id in model.encode(text, add_special_tokens=False)
        ]

    ids = encode_candidate(word)
    if len(ids) == 1:
        return int(ids[0]), word
    ids2 = encode_candidate(" " + word)
    if len(ids2) == 1:
        return int(ids2[0]), " " + word
    return None, ""


def validate_boundary_candidates(
    model: Any,
    candidate_words: Sequence[str],
    freq: np.ndarray,
    target_size: int,
    max_boundary_frequency: int,
    min_surface_len: int,
) -> Tuple[List[int], List[Dict[str, Any]]]:
    accepted_ids: List[int] = []
    accepted_set = set()
    report: List[Dict[str, Any]] = []
    special_ids = set(int(x) for x in model.all_special_ids)

    for word in candidate_words:
        token_id, encoded_form = word_to_single_token_id(model, word)
        row: Dict[str, Any] = {
            "candidate": word,
            "encoded_form": encoded_form,
            "accepted": False,
            "reason": "",
            "token_id": None if token_id is None else int(token_id),
            "decoded": None,
            "surface": None,
            "freq": None,
        }
        if token_id is None:
            row["reason"] = "not_single_token"
            report.append(row)
            continue
        decoded = model.decode([token_id], skip_special_tokens=False)
        surface = normalize_surface(decoded).strip()
        row["decoded"] = decoded
        row["surface"] = surface
        row["freq"] = int(freq[token_id])

        lower_surface = surface.lower()
        if token_id in special_ids:
            row["reason"] = "special_token"
        elif token_id in accepted_set:
            row["reason"] = "duplicate_token_id"
        elif len(surface) < int(min_surface_len):
            row["reason"] = "too_short"
        elif lower_surface in FORBIDDEN_BOUNDARY_SURFACES:
            row["reason"] = "forbidden_surface"
        elif not SURFACE_RE.fullmatch(surface):
            row["reason"] = "unclean_surface"
        elif int(freq[token_id]) > int(max_boundary_frequency):
            row["reason"] = "too_frequent_in_partition_prompts"
        else:
            row["accepted"] = True
            row["reason"] = "accepted"
            accepted_ids.append(int(token_id))
            accepted_set.add(int(token_id))
        report.append(row)
        if len(accepted_ids) >= int(target_size):
            break

    if len(accepted_ids) < int(target_size):
        raise RuntimeError(
            f"Only {len(accepted_ids)} boundary tokens accepted; need {target_size}. "
            "Add more candidates or relax filters explicitly."
        )
    return accepted_ids[: int(target_size)], report


def write_boundary_report_csv(report: Sequence[Dict[str, Any]], output_path: Path) -> None:
    if not report:
        return
    fieldnames = list(report[0].keys())
    with open(output_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report)


def main() -> None:
    args = parse_args()
    prompt_texts = load_prompt_lines(args.prompt_file)
    if not prompt_texts:
        raise RuntimeError(f"No prompts loaded from {args.prompt_file}")
    candidate_words = load_candidate_words(args.candidate_file)
    if not candidate_words:
        raise RuntimeError(f"No boundary candidates loaded from {args.candidate_file}")

    model = TokenizerOnlyLanguageModel(args.model_name)
    ecc_config = ECCConfig(block_len=args.block_len, vt_a=args.vt_a, target_boundary_pool=args.target_boundary_size)
    freq = build_token_frequency(model, prompt_texts)
    boundary_ids, boundary_report = validate_boundary_candidates(
        model=model,
        candidate_words=candidate_words,
        freq=freq,
        target_size=args.target_boundary_size,
        max_boundary_frequency=args.max_boundary_frequency,
        min_surface_len=args.min_surface_len,
    )
    partition = build_vocabulary_partition_from_boundary_ids(
        model=model,
        texts_for_frequency=prompt_texts,
        config=ecc_config,
        boundary_ids=boundary_ids,
        boundary_report=boundary_report,
    )
    output_dir = Path(args.output_dir)
    metadata = {
        "partition_version": "qwen3_fixed_partition_v1",
        "model_name": args.model_name,
        "prompt_file": args.prompt_file,
        "candidate_file": args.candidate_file,
        "num_partition_texts": len(prompt_texts),
        "target_boundary_size": args.target_boundary_size,
        "block_len": args.block_len,
        "vt_a": args.vt_a,
        "max_boundary_frequency": args.max_boundary_frequency,
        "min_surface_len": args.min_surface_len,
        "payload_split_source": "deterministic_hash_fallback_no_lm_weights",
    }
    save_vocabulary_partition(partition, output_dir, metadata=metadata)
    write_boundary_report_csv(boundary_report, output_dir / "boundary_report.csv")
    with open(output_dir / "boundary_candidates_qwen3_v1.txt", "w", encoding="utf-8") as handle:
        for word in candidate_words:
            handle.write(f"{word}\n")
    summary = {
        **metadata,
        "num_bucket0": len(partition.bucket0_ids),
        "num_bucket1": len(partition.bucket1_ids),
        "num_bucket2": len(partition.boundary_ids),
        "boundary_preview": [
            {
                "token_id": int(token_id),
                "decoded": model.decode([int(token_id)], skip_special_tokens=False),
                "surface": normalize_surface(model.decode([int(token_id)], skip_special_tokens=False)),
                "freq": int(freq[int(token_id)]),
            }
            for token_id in partition.boundary_ids[:25]
        ],
    }
    with open(output_dir / "bucket_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
