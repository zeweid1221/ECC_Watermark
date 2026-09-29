# Anchor-ECC

**Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes**

Zewei Deng, Muhammad Siddeek, Liyan Xie, Mohamed Seif, Mengdi Wang, H. Vincent Poor, Andrea Goldsmith

Anchor-ECC is an error-correcting-code-based watermarking framework for detecting and localizing sparse post-generation edits in watermarked LLM outputs. It maps generated tokens to structural symbols, constrains short blocks with joint Varshamov-Tenengolts and Hamming code properties, and uses global dynamic-programming decoding to recover edited block boundaries.

The repository contains the Anchor-ECC watermark implementation, its reproducibility utilities, and the companion project website. Paper and public website links will be added when the preprint is released. Separate exploratory projects and generated experiment artifacts are intentionally excluded.

## Evaluation Scope

The current experiment suite includes:

- Block-level detection and candidate edit localization under insertion, deletion, and substitution attacks.
- Adaptive and non-adaptive watermark generation across Qwen3-8B, Mistral-7B-Instruct-v0.3, and OPT-125M.
- Soft watermark strengths and approximate-hard operating points.
- Final-text-only global watermark verification against matched unwatermarked LLM outputs and human LFQA answers.
- A matched comparison with Combinatorial Watermarking under the same attack and block-level evaluation protocol.
- A readable synchronization-string plus VT baseline from the accepted Findings of EMNLP 2026 work, rerun under the current LFQA protocol.
- Qwen3-guided benign and malicious sparse edits on LFQA responses.

## Released Partition Protocols

The paper's main experiments use the `paper_main` partition strategy: 150
curated boundary anchors and the original group-local LSH payload split. Exact
model-specific artifacts are released under
`artifacts/partitions/compact150-semantic-v1/`. Rebuild this protocol with:

```bash
python scripts/build_model_partition.py \
  --model-profile <profile> \
  --prompt-file <lfqa-prompts> \
  --output-dir <output> \
  --target-boundary-size 150 \
  --payload-split-strategy paper_main
```

The appendix quality variant uses the `quality_variant_lsh` strategy. It assigns one
eighth of the eligible vocabulary to boundary symbols, balances the remainder
between the two payload buckets, and orients LSH groups to improve global count
and calibration-frequency balance. Build it with
`--boundary-vocab-fraction 0.125 --payload-split-strategy quality_variant_lsh`. When the
strategy flag is omitted, the builder infers `paper_main` for an explicit fixed
boundary count and `quality_variant_lsh` for the fractional protocol.

Both protocols use adaptive codeword completion with nearest-feasible recovery
if a soft-watermark error makes the current payload prefix infeasible. See
`msi/README_BOUNDARY_EIGHTH.md` for the three-model Slurm pipeline used for the
quality-variant ablation.

## Repository Structure

- `watermark_project/`: ECC generation, vocabulary partitioning, decoding, edit simulation, evaluation, and shared model utilities.
- `artifacts/partitions/`: exact compact-150 vocabulary partitions used for the paper's main experiments.
- `baselines/`: independent Combinatorial Watermark and accepted sync-ECC baselines.
- `scripts/`: experiment runners, LLM editor and judge pipelines, plotting, diagnostics, and result-processing utilities.
- `tests/`: regression and protocol tests for generation, partition identity, detector provenance, and evaluation behavior.
- `resources/`: fixed boundary-token candidates and model-specific supporting resources.
- `msi/`: Slurm launchers and environment helpers used for MSI GPU experiments.
- `website/`: Vite and React companion website with precomputed result tables and interactive walkthrough examples.
- `run_main.py`: primary command-line entry point for watermark experiments.

Large model caches, generated dependency folders, and full experiment artifacts are intentionally excluded from version control.

## Python Setup

Create an isolated environment and install the project dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Inspect the available experiment arguments with:

```bash
python run_main.py --help
```

Run the protocol regression suite with:

```bash
python -m unittest discover -s tests -v
```

GPU experiments require a compatible PyTorch/CUDA environment. Model-specific vocabulary partitions must be built with the corresponding tokenizer and model profile rather than reused across model families.

The accepted synchronization-string plus VT comparison is documented in
`msi/README_SYNC_ECC_LFQA.md`. Its implementation is intentionally separate
from the current Anchor-ECC core so that the baseline and proposed method cannot
silently share detector state. Saved baseline generations can be reevaluated
with `scripts/recompute_sync_ecc_lfqa_results.py`; the replay verifies every
deterministic attack against the original row-level artifacts before emitting
corrected metrics.

CW operating points can be reproduced with
`scripts/recompute_combinatorial_original_threshold.py`. Calibration uses the
original strict token-level decision rule and clean outputs only. If the
Type-I 0.1 calibration selects the degenerate threshold zero, the script
selects the first positive value on the discrete CW score lattice and records
the realized clean-token alarm rate.

## Website

Run the companion website locally with:

```bash
cd website
npm ci
npm run dev
```

Vite will print the local preview URL, typically `http://localhost:5173/`.

Create a static production build with:

```bash
npm run build
```

The deployable website is written to `website/dist/`. The browser walkthrough replays saved experiment metadata and does not run model inference or live watermark detection.

## Citation

The canonical arXiv citation will be added when the preprint becomes publicly available. Until then, the provisional project citation is:

```bibtex
@misc{deng2026anchorecc,
  title  = {Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes},
  author = {Deng, Zewei and Siddeek, Muhammad and Xie, Liyan and Seif, Mohamed and Wang, Mengdi and Poor, H. Vincent and Goldsmith, Andrea},
  year   = {2026}
}
```
