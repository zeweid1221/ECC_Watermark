from __future__ import annotations

import argparse
import re
from pathlib import Path

from datasets import Dataset, load_dataset


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).replace("\n", " ").replace("\r", " ")).strip()


def is_englishish(text: str) -> bool:
    if re.search(r"[^\x00-\x7F]", text):
        return False
    letters = sum(ch.isalpha() for ch in text)
    return letters >= 20


def is_clean_prompt_text(text: str, *, exclude_sensitive: bool) -> bool:
    if re.search(r"\[deleted\]|_URL_|https?://|www\.", text, flags=re.IGNORECASE):
        return False
    if exclude_sensitive and re.search(
        r"\b(fuck|porn|rape|semen|orgasm|fetish|ass|shit)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    return True


def iter_local_arrow_rows(dataset_name: str, split: str):
    cache_root = Path.home() / ".cache" / "huggingface" / "datasets"
    dataset_dir = cache_root / dataset_name.replace("/", "___")
    if not dataset_dir.exists():
        return None
    arrow_files = sorted(dataset_dir.rglob(f"*{split}*.arrow"))
    if not arrow_files:
        return None

    def _rows():
        for arrow_file in arrow_files:
            ds = Dataset.from_file(str(arrow_file))
            for row in ds:
                yield row

    return _rows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export small English LFQA prompts for generation quality screening.")
    parser.add_argument("--dataset", default="vblagoje/lfqa")
    parser.add_argument("--split", default="train")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--output", default="outputs/text_quality_lfqa_screen/lfqa_prompts_8.txt")
    parser.add_argument("--max-context-chars", type=int, default=500)
    parser.add_argument(
        "--exclude-sensitive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip prompts with obvious profanity or sexual/graphic terms.",
    )
    parser.add_argument(
        "--prefer-local-arrow-cache",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Prefer already-cached HF Arrow files over load_dataset for fast prompt extraction.",
    )
    args = parser.parse_args()

    rows = iter_local_arrow_rows(args.dataset, args.split) if args.prefer_local_arrow_cache else None
    if rows is None:
        rows = load_dataset(args.dataset, split=args.split)

    prompts = []
    for row in rows:
        title = clean(row.get("title", ""))
        body = clean(row.get("selftext", ""))
        combined = f"{title} {body}".strip()
        if not title or len(title) < 20 or len(title) > 220:
            continue
        if not is_englishish(combined):
            continue
        if not is_clean_prompt_text(combined, exclude_sensitive=args.exclude_sensitive):
            continue
        prompt = title
        if body:
            prompt = f"{title} Context: {body[: args.max_context_chars]}"
        if not is_clean_prompt_text(prompt, exclude_sensitive=args.exclude_sensitive):
            continue
        prompts.append(prompt)
        if len(prompts) >= args.count:
            break

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(prompts), encoding="utf-8")
    print(output_path)
    print(f"num_prompts={len(prompts)}")
    for idx, prompt in enumerate(prompts, start=1):
        print(f"{idx}. {prompt[:180]}")


if __name__ == "__main__":
    main()
