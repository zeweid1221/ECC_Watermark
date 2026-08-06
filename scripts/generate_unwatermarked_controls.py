from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.preview_watermarked_generation_quality import (  # noqa: E402
    build_preview_language_model,
    build_user_prompt,
    generate_unwatermarked_preview,
    load_prompt_lines,
    render_prompt_for_model,
    start_preview_session,
)
from watermark_project.config import DEFAULT_SYSTEM_PROMPT, ModelConfig  # noqa: E402
from watermark_project.io_utils import ensure_dir, write_json  # noqa: E402
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile  # noqa: E402
from watermark_project.modeling import stable_hash_int  # noqa: E402
from watermark_project.ppl import compute_generation_perplexities  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate matched unwatermarked controls without running ECC generation."
    )
    parser.add_argument("--backend", choices=["mock", "hf"], default="hf")
    parser.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), default=None)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--use-8bit", action="store_true")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--num-samples", type=int, default=256)
    parser.add_argument("--target-new-tokens", type=int, default=144)
    parser.add_argument("--max-prompt-tokens", type=int, default=256)
    parser.add_argument("--prompt-style", choices=["qa", "plain"], default="qa")
    parser.add_argument(
        "--use-chat-template",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument("--enable-thinking", action="store_true")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--sampling", choices=["sample", "greedy"], default="sample")
    parser.add_argument("--temperature", type=float, default=0.75)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--repetition-penalty", type=float, default=1.2)
    parser.add_argument(
        "--english-token-filter",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2043,
        help="Adaptive ECC setting seed: generation_seed 2026 + adaptive offset 17.",
    )
    parser.add_argument(
        "--compute-ppl",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
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
    if profile:
        args.prompt_style = profile.prompt_style
        if args.use_chat_template is None:
            args.use_chat_template = profile.use_chat_template
        args.enable_thinking = profile.enable_thinking
    elif args.use_chat_template is None:
        args.use_chat_template = False
    if args.target_new_tokens <= 0:
        parser.error("--target-new-tokens must be positive.")
    return args


def read_checkpoint(path: Path) -> Dict[int, Dict[str, Any]]:
    if not path.exists():
        return {}
    records: Dict[int, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid checkpoint JSON at {path}:{line_number}."
                ) from exc
            records[int(record["sample_index"])] = record
    return records


def append_checkpoint(path: Path, record: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def prompt_token_ids(model: Any, rendered_prompt: str, prompt_mode: str) -> List[int]:
    session = start_preview_session(model, rendered_prompt, prompt_mode)
    return [int(x) for x in session.prompt_ids]


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    ensure_dir(str(output_dir))
    checkpoint_path = output_dir / "unwatermarked_checkpoint.jsonl"
    if checkpoint_path.exists() and not args.resume:
        raise FileExistsError(
            f"Checkpoint already exists and --no-resume was requested: {checkpoint_path}"
        )

    prompts = load_prompt_lines(args.prompt_file)[: args.num_samples]
    if len(prompts) != args.num_samples:
        raise ValueError(
            f"Requested {args.num_samples} prompts, but loaded {len(prompts)} from {args.prompt_file}."
        )
    model = build_preview_language_model(
        ModelConfig(
            backend=args.backend,
            model_name=args.model_name,
            model_profile=args.model_profile,
            device=args.device,
            max_prompt_tokens=args.max_prompt_tokens,
            use_4bit=args.use_4bit,
            use_8bit=args.use_8bit,
        ),
        corpus_texts=prompts,
    )
    records = read_checkpoint(checkpoint_path) if args.resume else {}
    for sample_index, raw_prompt in enumerate(prompts):
        if sample_index in records:
            continue
        user_prompt = build_user_prompt(raw_prompt, args.prompt_style)
        rendered_prompt, prompt_mode = render_prompt_for_model(
            model=model,
            user_prompt=user_prompt,
            system_prompt=args.system_prompt,
            use_chat_template=bool(args.use_chat_template),
            enable_thinking=bool(args.enable_thinking),
        )
        prompt_ids = prompt_token_ids(model, rendered_prompt, prompt_mode)
        sample_seed = (
            int(args.seed) + stable_hash_int(rendered_prompt)
        ) % (2**32)
        text, generated_ids = generate_unwatermarked_preview(
            model=model,
            rendered_prompt=rendered_prompt,
            prompt_mode=prompt_mode,
            args=args,
            sample_seed=sample_seed,
            target_new_tokens=args.target_new_tokens,
        )
        record = {
            "sample_index": sample_index,
            "raw_prompt": raw_prompt,
            "user_prompt": user_prompt,
            "rendered_prompt": rendered_prompt,
            "prompt_mode": prompt_mode,
            "sample_seed": sample_seed,
            "unwatermarked_text": text,
            "prompt_token_ids": prompt_ids,
            "generated_token_ids": [int(x) for x in generated_ids],
            "num_generated_tokens": len(generated_ids),
        }
        append_checkpoint(checkpoint_path, record)
        records[sample_index] = record
        if (sample_index + 1) % 10 == 0 or sample_index + 1 == len(prompts):
            print(f"[progress] {sample_index + 1}/{len(prompts)}", flush=True)

    ordered = [records[index] for index in range(len(prompts))]
    ppl_metrics: Dict[str, float] = {}
    if args.compute_ppl:
        ppl_metrics = compute_generation_perplexities(
            model,
            prompt_token_ids=[record["prompt_token_ids"] for record in ordered],
            generated_token_ids=[record["generated_token_ids"] for record in ordered],
        )
    csv_rows = []
    for record in ordered:
        csv_rows.append(
            {
                **{
                    key: value
                    for key, value in record.items()
                    if key not in {"prompt_token_ids", "generated_token_ids"}
                },
                "prompt_token_ids_json": json.dumps(record["prompt_token_ids"]),
                "generated_token_ids_json": json.dumps(record["generated_token_ids"]),
                **ppl_metrics,
            }
        )

    csv_path = output_dir / "unwatermarked_generations.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    write_json(str(output_dir / "unwatermarked_generations.json"), ordered)
    write_json(
        str(output_dir / "unwatermarked_config.json"),
        {
            "args": vars(args),
            "num_completed": len(ordered),
            "ppl_metrics": ppl_metrics,
            "seed_definition": "seed + stable_hash_int(rendered_prompt)",
            "watermark_enabled": False,
        },
    )
    print(f"Saved {len(ordered)} controls to {csv_path}")
    print(json.dumps(ppl_metrics, indent=2))


if __name__ == "__main__":
    main()
