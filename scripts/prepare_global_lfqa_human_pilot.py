from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

try:
    from datasets import Dataset
    from transformers import AutoTokenizer
except Exception as exc:  # pragma: no cover
    raise RuntimeError("datasets and transformers are required for this script.") from exc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_lfqa_quality_prompts import clean  # noqa: E402
from watermark_project.model_profiles import get_model_profile  # noqa: E402


DEFAULT_PROFILES = (
    "qwen3-8b",
    "mistral-7b-instruct-v0.3",
    "opt-125m",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare matched watermarked and LFQA-human global-verification inputs."
    )
    parser.add_argument("--results-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--lfqa-cache-dir", default=None)
    parser.add_argument("--model-profiles", default=",".join(DEFAULT_PROFILES))
    parser.add_argument("--setting-key", default="ecc_soft_adaptive_bias20")
    parser.add_argument("--watermark-source-type", default=None)
    parser.add_argument("--num-samples", type=int, default=256)
    parser.add_argument("--max-context-chars", type=int, default=500)
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def lfqa_arrow_files(cache_dir: str | None) -> List[Path]:
    root = (
        Path(cache_dir)
        if cache_dir
        else Path.home() / ".cache" / "huggingface" / "datasets" / "vblagoje___lfqa"
    )
    files = sorted(root.rglob("*train*.arrow"))
    if not files:
        raise FileNotFoundError(f"No LFQA train Arrow files found under {root}.")
    return files


def iter_lfqa_rows(files: Iterable[Path]) -> Iterable[Dict[str, Any]]:
    for path in files:
        dataset = Dataset.from_file(str(path))
        yield from dataset


def reconstruct_prompt(row: Dict[str, Any], max_context_chars: int) -> str | None:
    title = clean(row.get("title", ""))
    body = clean(row.get("selftext", ""))
    if not title:
        return None
    return title if not body else f"{title} Context: {body[:max_context_chars]}"


def normalize_english_answer(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
    }
    normalized = str(text)
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = unicodedata.normalize("NFKD", normalized)
    return clean(normalized.encode("ascii", errors="ignore").decode("ascii"))


def human_answer_candidates(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    answers = row.get("answers") or {}
    texts = list(answers.get("text") or [])
    scores = list(answers.get("score") or [])
    candidates = []
    for text, score in zip(texts, scores):
        answer = normalize_english_answer(text)
        if len(answer) < 20 or sum(ch.isalpha() for ch in answer) < 20:
            continue
        candidates.append(
            {
                "answer": answer,
                "score": int(score or 0),
            }
        )
    return sorted(
        candidates,
        key=lambda item: (item["score"], len(item["answer"])),
        reverse=True,
    )


def load_setting(path: Path, setting_key: str) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches = [
        setting
        for setting in payload["settings"]
        if setting.get("setting_key") == setting_key
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one setting {setting_key!r} in {path}, found {len(matches)}."
        )
    return list(matches[0]["generated"])


def collect_human_answers(
    target_prompts: set[str],
    files: Iterable[Path],
    max_context_chars: int,
) -> Dict[str, Dict[str, Any]]:
    found: Dict[str, Dict[str, Any]] = {}
    for row in iter_lfqa_rows(files):
        prompt = reconstruct_prompt(row, max_context_chars)
        if prompt not in target_prompts or prompt in found:
            continue
        candidates = human_answer_candidates(row)
        if candidates:
            found[prompt] = {
                "q_id": str(row.get("q_id", "")),
                "candidates": candidates,
            }
        if len(found) == len(target_prompts):
            break
    return found


def main() -> None:
    args = parse_args()
    results_root = Path(args.results_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    profiles = [item.strip() for item in args.model_profiles.split(",") if item.strip()]
    watermark_source_type = args.watermark_source_type or f"watermarked_{args.setting_key}"
    arrow_files = lfqa_arrow_files(args.lfqa_cache_dir)

    generated_by_profile: Dict[str, List[Dict[str, Any]]] = {}
    target_prompts: set[str] = set()
    for profile_key in profiles:
        generated = load_setting(
            results_root / profile_key / "detailed_results.json",
            args.setting_key,
        )[: args.num_samples]
        generated_by_profile[profile_key] = generated
        target_prompts.update(str(item["prompt"]) for item in generated)

    human_answers = collect_human_answers(
        target_prompts,
        arrow_files,
        args.max_context_chars,
    )
    manifest: List[Dict[str, Any]] = []
    for profile_key in profiles:
        profile = get_model_profile(profile_key)
        tokenizer = AutoTokenizer.from_pretrained(
            profile.model_name,
            use_fast=True,
            local_files_only=args.local_files_only,
        )
        rows: List[Dict[str, Any]] = []
        skipped_missing = 0
        length_matched = 0
        shorter_human = 0
        paired_count = 0
        for source_index, item in enumerate(generated_by_profile[profile_key]):
            prompt = str(item["prompt"])
            human = human_answers.get(prompt)
            watermarked_text = str(item["suffix_text"])
            watermarked_ids = tokenizer.encode(
                watermarked_text,
                add_special_tokens=False,
            )
            pair_id = f"{profile_key}_{source_index}"
            common = {
                "pair_id": pair_id,
                "prompt": prompt,
                "watermarked_num_tokens": len(watermarked_ids),
            }
            rows.append(
                {
                    "sample_id": f"{pair_id}_watermarked",
                    "source_type": watermark_source_type,
                    "label": 1,
                    "text": watermarked_text,
                    "lfqa_q_id": human["q_id"] if human else "",
                    **common,
                }
            )
            if human is None:
                skipped_missing += 1
                continue
            encoded_candidates = [
                (
                    candidate,
                    tokenizer.encode(
                        candidate["answer"],
                        add_special_tokens=False,
                    ),
                )
                for candidate in human["candidates"]
            ]
            long_enough = [
                item
                for item in encoded_candidates
                if len(item[1]) >= len(watermarked_ids)
            ]
            selected_candidate, human_ids = (
                long_enough[0]
                if long_enough
                else encoded_candidates[0]
            )
            if len(human_ids) >= len(watermarked_ids):
                matched_human_ids = human_ids[: len(watermarked_ids)]
                length_match_mode = "truncated_to_watermarked_token_length"
                length_matched += 1
            else:
                matched_human_ids = human_ids
                length_match_mode = "shorter_original_human_answer"
                shorter_human += 1
            matched_human_text = tokenizer.decode(
                matched_human_ids,
                skip_special_tokens=True,
            )
            rows.append(
                {
                    "sample_id": f"{pair_id}_human",
                    "source_type": "lfqa_human",
                    "label": 0,
                    "text": matched_human_text,
                    "lfqa_q_id": human["q_id"],
                    "human_answer_score": selected_candidate["score"],
                    "human_num_tokens": len(matched_human_ids),
                    "length_match_mode": length_match_mode,
                    **common,
                }
            )
            paired_count += 1

        output_dir = output_root / profile_key
        output_dir.mkdir(parents=True, exist_ok=True)
        output_csv = output_dir / "global_verification_input.csv"
        pd.DataFrame(rows).to_csv(output_csv, index=False)
        manifest.append(
            {
                "model_profile": profile_key,
                "model_name": profile.model_name,
                "setting_key": args.setting_key,
                "watermark_source_type": watermark_source_type,
                "num_watermarked": len(generated_by_profile[profile_key]),
                "num_human": paired_count,
                "num_pairs": paired_count,
                "num_rows": len(rows),
                "skipped_missing_human_answer": skipped_missing,
                "num_length_matched_pairs": length_matched,
                "num_shorter_human_pairs": shorter_human,
                "input_csv": str(output_csv),
            }
        )

    (output_root / "input_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
