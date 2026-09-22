from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build_qwen3_fixed_partition import (  # noqa: E402
    DEFAULT_CANDIDATE_FILE,
    load_candidate_words,
    validate_boundary_candidates,
    write_boundary_report_csv,
)
from preview_watermarked_generation_quality import load_prompt_lines  # noqa: E402
from watermark_project.config import ECCConfig, ModelConfig  # noqa: E402
from watermark_project.model_profiles import MODEL_PROFILES, get_model_profile  # noqa: E402
from watermark_project.modeling import build_language_model  # noqa: E402
from watermark_project.partitioning import (  # noqa: E402
    build_token_frequency,
    build_vocabulary_partition,
    build_vocabulary_partition_from_boundary_ids,
    partition_checksum,
    save_vocabulary_partition,
    validate_vocabulary_partition,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one model-specific ECC partition using the active model embeddings."
    )
    parser.add_argument("--model-profile", choices=sorted(MODEL_PROFILES), required=True)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--backend", choices=["hf", "mock"], default="hf")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--candidate-file", default=str(DEFAULT_CANDIDATE_FILE))
    parser.add_argument("--output-dir", required=True)
    boundary_group = parser.add_mutually_exclusive_group()
    boundary_group.add_argument(
        "--boundary-vocab-fraction",
        type=float,
        default=1.0 / 8.0,
        help="Fraction of eligible vocabulary assigned to boundary symbols (default: 1/8).",
    )
    boundary_group.add_argument(
        "--target-boundary-size",
        type=int,
        default=None,
        help=(
            "Fixed boundary count used by the compact-anchor paper protocol; "
            "overrides the fractional protocol when specified."
        ),
    )
    parser.add_argument("--max-boundary-frequency", type=int, default=50)
    parser.add_argument("--min-surface-len", type=int, default=3)
    parser.add_argument("--block-len", type=int, default=7)
    parser.add_argument("--vt-a", type=int, default=6)
    parser.add_argument("--lsh-bits", type=int, default=12)
    parser.add_argument(
        "--payload-split-strategy",
        choices=("paper_main", "quality_variant_lsh"),
        default=None,
        help=(
            "Payload assignment algorithm. Defaults to paper_main with an explicit fixed "
            "boundary count and quality_variant_lsh with the fractional boundary protocol."
        ),
    )
    parser.add_argument("--allow-hash-fallback", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = get_model_profile(args.model_profile)
    model_name = args.model_name or profile.model_name
    if model_name != profile.model_name:
        raise ValueError(
            f"Profile {profile.key!r} is tied to {profile.model_name!r}, not {model_name!r}."
        )
    prompt_texts = load_prompt_lines(args.prompt_file)
    if not prompt_texts:
        raise RuntimeError(f"No prompts loaded from {args.prompt_file}")
    model = build_language_model(
        ModelConfig(
            backend=args.backend,
            model_name=model_name,
            model_profile=profile.key,
            device=args.device,
            use_4bit=args.use_4bit,
            max_prompt_tokens=256,
        ),
        corpus_texts=prompt_texts,
    )
    payload_split_strategy = args.payload_split_strategy or (
        "paper_main" if args.target_boundary_size is not None else "quality_variant_lsh"
    )
    ecc_config = ECCConfig(
        block_len=args.block_len,
        vt_a=args.vt_a,
        target_boundary_pool=args.target_boundary_size,
        boundary_vocab_fraction=args.boundary_vocab_fraction,
        lsh_bits=args.lsh_bits,
        payload_split_strategy=payload_split_strategy,
    )
    if args.target_boundary_size is None:
        partition = build_vocabulary_partition(
            model=model,
            texts_for_frequency=prompt_texts,
            config=ecc_config,
        )
        boundary_report = partition.boundary_report
        candidate_file = None
    else:
        candidate_words = load_candidate_words(args.candidate_file)
        if not candidate_words:
            raise RuntimeError(f"No boundary candidates loaded from {args.candidate_file}")
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
        candidate_file = str(Path(args.candidate_file))
    if (
        partition.metadata.get("payload_split_source") != "embedding_lsh"
        and not args.allow_hash_fallback
    ):
        raise RuntimeError(
            "The active model did not expose input embeddings. Refusing to save a non-semantic "
            "partition without --allow-hash-fallback."
        )
    validate_vocabulary_partition(
        partition,
        model,
        require_semantic_split=not args.allow_hash_fallback,
    )

    output_dir = Path(args.output_dir)
    protocol_name = (
        "compact150_paper_main"
        if payload_split_strategy == "paper_main" and len(partition.boundary_ids) == 150
        else "quality_variant_lsh_boundary_fraction"
        if payload_split_strategy == "quality_variant_lsh" and args.target_boundary_size is None
        else payload_split_strategy
    )
    metadata = {
        "partition_protocol": protocol_name,
        "payload_split_strategy": payload_split_strategy,
        "model_profile": profile.key,
        "model_name": model_name,
        "prompt_file": str(Path(args.prompt_file)),
        "candidate_file": candidate_file,
        "num_partition_texts": len(prompt_texts),
        "target_boundary_size": len(partition.boundary_ids),
        "target_boundary_size_requested": args.target_boundary_size,
        "boundary_vocab_fraction": (
            args.boundary_vocab_fraction if args.target_boundary_size is None else None
        ),
        "block_len": args.block_len,
        "vt_a": args.vt_a,
        "lsh_bits": args.lsh_bits,
        "max_boundary_frequency": args.max_boundary_frequency,
        "min_surface_len": args.min_surface_len,
    }
    save_vocabulary_partition(partition, output_dir, metadata=metadata)
    write_boundary_report_csv(boundary_report, output_dir / "boundary_report.csv")
    summary = {
        **partition.metadata,
        **metadata,
        "partition_checksum_sha256": partition_checksum(partition),
        "num_bucket0": len(partition.bucket0_ids),
        "num_bucket1": len(partition.bucket1_ids),
        "num_bucket2": len(partition.boundary_ids),
        "num_banned": len(partition.banned_ids),
    }
    with open(output_dir / "bucket_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
