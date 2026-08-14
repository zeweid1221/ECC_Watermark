# Boundary-Eighth ECC Rerun

This pipeline uses the ECC project's native semantic partition builder with:

- boundary symbols: one eighth of the eligible vocabulary;
- payload symbols: the remaining vocabulary divided evenly;
- ECC generation: adaptive by default;
- invalid-prefix recovery: nearest feasible continuation;
- biases: 2, 5, and 20;
- 256 prompts, 18 closed blocks, and the existing synthetic and LLM-guided edit protocols.

All outputs use new paths under `outputs/ecc_boundary_eighth_20260813` and do not overwrite the previous 150-token-boundary results.

## Submit

```bash
cd ~/EMNLP
source msi/activate_env.sh
python -m unittest tests.test_boundary_fraction_protocol tests.test_three_model_refactor -v
bash msi/submit_boundary_eighth_pipeline.sh
```

## Monitor

```bash
cat outputs/ecc_boundary_eighth_20260813/submitted_jobs.txt
squeue -u "$USER"
```

## Validate the ECC sweep

```bash
python scripts/validate_boundary_eighth_results.py
```
