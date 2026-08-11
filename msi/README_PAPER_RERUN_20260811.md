# Paper rerun: corrected PPL + nearest-feasible ECC

This rerun is isolated under `outputs/paper_rerun_20260811/`. It does not
overwrite any earlier paper results.

## Included jobs

- Adaptive ECC generation and synthetic edit detection for Qwen3-8B,
  Mistral-7B-Instruct-v0.3, and OPT-125M at logit biases 2, 5, 20, and 50.
- Non-adaptive generation at the same four biases for the adaptive PPL ablation.
- Matched unwatermarked controls with 144 generated tokens.
- Qwen3-guided benign/malicious LLM edits for every source-model/bias pair.

Every adaptive ECC source uses `nearest_feasible`. PPL is recomputed from the
exact saved token IDs both with and without the rendered question/chat prompt.
Repetition penalty is applied before watermark control.

## Submit

```bash
cd ~/EMNLP
mkdir -p logs
source msi/activate_env.sh
python -m unittest tests.test_bucket_compatibility tests.test_three_model_refactor -v
bash msi/submit_paper_rerun_20260811.sh
```

The four job IDs are saved in:

```text
outputs/paper_rerun_20260811/submitted_jobs.txt
```

The clean-control and LLM-editor arrays wait for the adaptive source array.
The non-adaptive quality array can run in parallel.

## Validate

Run each stage as it completes:

```bash
python scripts/validate_paper_rerun_20260811.py --stage source
python scripts/validate_paper_rerun_20260811.py --stage quality
python scripts/validate_paper_rerun_20260811.py --stage clean
python scripts/validate_paper_rerun_20260811.py --stage editor
```

After all jobs finish:

```bash
python scripts/validate_paper_rerun_20260811.py --stage all
tar -czf paper_rerun_20260811_results.tar.gz outputs/paper_rerun_20260811
```
