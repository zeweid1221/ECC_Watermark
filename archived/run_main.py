from __future__ import annotations

import argparse
import os
from typing import List

import pandas as pd

from watermark_project.config import ModelConfig, PromptConfig, RunConfig
from watermark_project.experiment import run_experiment
from watermark_project.io_utils import ensure_dir


SMOKE_PROMPTS = [
    "Large language models are often evaluated under post generation edits, so a robust watermark needs to preserve recoverable structure without making the text obviously unnatural.",
    "Adaptive watermarking can reduce distortion because the model keeps more lexical freedom while each partial block remains compatible with at least one feasible codeword continuation.",
    "A practical baseline experiment should compare ECC and KGW under the same prompts, the same generation budget, the same edit protocol, and the same saved result tables.",
    "Perplexity matters in this project because robustness alone is not enough; the watermark should also preserve fluent, low distortion text generation under hard and soft controls.",
]


def parse_csv_floats(value: str) -> List[float]:
    return [float(x.strip()) for x in value.split(",") if x.strip()]


def parse_csv_ints(value: str) -> List[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def parse_csv_strs(value: str) -> List[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def build_smoke_config(
    output_dir: str,
    device: str = "cpu",
    backend: str = "mock",
    model_name: str = "mock-lm",
    use_4bit: bool = False,
) -> RunConfig:
    return RunConfig(
        output_dir=output_dir,
        model=ModelConfig(
            backend=backend,
            model_name=model_name,
            device=device,
            max_prompt_tokens=96,
            mock_vocab_size=220,
            use_4bit=use_4bit,
        ),
        prompts=PromptConfig(inline_prompts=SMOKE_PROMPTS, prompt_count=4, prompt_seed=42),
        schemes=["ecc", "kgw"],
        watermark_modes=["hard", "soft"],
        ecc_adaptive_modes=[True, False],
        edit_rates=[0.2, 0.4],
        target_blocks=4,
        max_new_tokens=96,
        attack_max_edits_per_block=1,
        attack_max_edits_per_blocks=[1],
        decoder_max_edits_per_block=1,
        edit_count_mode="uniform_1_to_k",
        run_name="smoke_test",
        save_parquet=True,
        save_detailed_json=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified ECC/KGW watermark experiment runner.")
    parser.add_argument("--output-dir", type=str, default="outputs/main_run")
    parser.add_argument("--backend", type=str, choices=["mock", "hf"], default="mock")
    parser.add_argument("--model-name", type=str, default="mock-lm")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--prompt-file", type=str, default=None)
    parser.add_argument("--schemes", type=str, default="ecc,kgw")
    parser.add_argument("--watermark-modes", type=str, default="hard,soft")
    parser.add_argument("--ecc-adaptive-modes", type=str, default="true,false")
    parser.add_argument("--edit-rates", type=str, default="0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8")
    parser.add_argument("--target-blocks", type=int, default=8)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--prompt-count", type=int, default=8)
    parser.add_argument("--attack-max-edits-per-block", type=int, default=1)
    parser.add_argument("--attack-max-edits-per-blocks", type=str, default=None)
    parser.add_argument("--decoder-max-edits-per-block", type=int, default=3)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    ensure_dir(args.output_dir)
    if args.smoke_test:
        cfg = build_smoke_config(
            args.output_dir,
            device=args.device,
            backend=args.backend,
            model_name=args.model_name,
            use_4bit=args.use_4bit,
        )
    else:
        adaptive_modes = [x.strip().lower() == "true" for x in args.ecc_adaptive_modes.split(",") if x.strip()]
        prompt_cfg = PromptConfig(
            inline_prompts=tuple(SMOKE_PROMPTS if args.backend == "mock" and not args.prompt_file else ()),
            prompt_text_file=args.prompt_file,
            prompt_count=args.prompt_count,
            prompt_seed=42,
        )
        cfg = RunConfig(
            output_dir=args.output_dir,
            model=ModelConfig(
                backend=args.backend,
                model_name=args.model_name,
                device=args.device,
                max_prompt_tokens=96,
                mock_vocab_size=220,
                use_4bit=args.use_4bit,
            ),
            prompts=prompt_cfg,
            schemes=parse_csv_strs(args.schemes),
            watermark_modes=parse_csv_strs(args.watermark_modes),
            ecc_adaptive_modes=adaptive_modes or [True, False],
            edit_rates=parse_csv_floats(args.edit_rates),
            target_blocks=args.target_blocks,
            max_new_tokens=args.max_new_tokens,
            attack_max_edits_per_block=args.attack_max_edits_per_block,
            attack_max_edits_per_blocks=(
                parse_csv_ints(args.attack_max_edits_per_blocks)
                if args.attack_max_edits_per_blocks
                else [args.attack_max_edits_per_block]
            ),
            decoder_max_edits_per_block=args.decoder_max_edits_per_block,
        )

    result = run_experiment(cfg)
    summary_df: pd.DataFrame = result["summary_df"]
    print("\nSummary rows:")
    print(summary_df.to_string(index=False))
    if args.smoke_test:
        smoke_note_path = os.path.join(args.output_dir, "smoke_test_note.txt")
        with open(smoke_note_path, "w", encoding="utf-8") as handle:
            handle.write("Smoke test settings\n")
            handle.write(f"backend={cfg.model.backend}\n")
            handle.write(f"requested_device={cfg.model.device}\n")
            handle.write(f"resolved_device={result.get('model_device')}\n")
            handle.write(f"requested_use_4bit={cfg.model.use_4bit}\n")
            handle.write(f"actual_use_4bit={result.get('used_4bit')}\n")
            handle.write(f"quantization_mode={result.get('quantization_mode')}\n")
            handle.write(f"model_name={cfg.model.model_name}\n")
            handle.write(f"schemes={cfg.schemes}\n")
            handle.write(f"watermark_modes={cfg.watermark_modes}\n")
            handle.write(f"ecc_adaptive_modes={cfg.ecc_adaptive_modes}\n")
            handle.write(f"edit_rates={cfg.edit_rates}\n")
            handle.write(f"target_blocks={cfg.target_blocks}\n")
            handle.write(f"max_new_tokens={cfg.max_new_tokens}\n")
            handle.write(f"attack_max_edits_per_block={cfg.attack_max_edits_per_block}\n")
            handle.write(f"attack_max_edits_per_blocks={cfg.attack_max_edits_per_blocks}\n")
            handle.write(f"decoder_max_edits_per_block={cfg.decoder_max_edits_per_block}\n")
            handle.write(f"prompts={len(result['prompts'])}\n")
        print(f"\nSmoke test note saved to: {smoke_note_path}")


if __name__ == "__main__":
    main()
