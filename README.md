# ECC-IW

**Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes**

Zewei Deng, Muhammad Siddeek, Liyan Xie, Mohamed S Mohamed, Mengdi Wang, H. Vincent Poor, Andrea Goldsmith

ECC-IW is an error-correcting-code-based watermarking framework for detecting and localizing sparse post-generation edits in watermarked LLM outputs. It maps generated tokens to structural symbols, constrains short blocks with joint Varshamov-Tenengolts and Hamming code properties, and uses global dynamic-programming decoding to recover edited block boundaries.

The repository contains the ECC-IW watermark implementation, its reproducibility utilities, and the companion project website. Paper and public website links will be added when the preprint is released. Separate exploratory projects and generated experiment artifacts are intentionally excluded.

## Evaluation Scope

The current experiment suite includes:

- Block-level detection and candidate edit localization under insertion, deletion, and substitution attacks.
- Adaptive and non-adaptive watermark generation across Qwen3-8B, Mistral-7B-Instruct-v0.3, and OPT-125M.
- Soft watermark strengths and approximate-hard operating points.
- Final-text-only global watermark verification against matched unwatermarked LLM outputs and human LFQA answers.
- A matched comparison with Combinatorial Watermarking under the same attack and block-level evaluation protocol.
- Qwen3-guided benign and malicious sparse edits on LFQA responses.

## Repository Structure

- `watermark_project/`: ECC generation, vocabulary partitioning, decoding, edit simulation, evaluation, and shared model utilities.
- `baselines/`: KGW-based and Combinatorial Watermark baselines.
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

GPU experiments require a compatible PyTorch/CUDA environment. Model-specific vocabulary partitions must be built with the corresponding tokenizer and model profile rather than reused across model families.

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
@misc{deng2026ecciw,
  title  = {ECC-IW: Local Integrity Checking for Watermarked LLM Outputs via Error-Correcting Codes},
  author = {Deng, Zewei and Siddeek, Muhammad and Xie, Liyan and Mohamed, Mohamed S and Wang, Mengdi and Poor, H. Vincent and Goldsmith, Andrea},
  year   = {2026}
}
```
