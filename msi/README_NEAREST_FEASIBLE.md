# Nearest-feasible recovery experiment

This experiment is opt-in. Existing commands retain the default
`legacy_unconstrained` behavior. The new sweep passes
`--adaptive-invalid-prefix-policy nearest_feasible` explicitly.

## Jobs

- `run_three_model_ecc_nearest_feasible.slurm`: Qwen3-8B, Mistral-7B-Instruct-v0.3,
  and OPT-125M; adaptive soft ECC at logit biases 2, 5, and 20. Detection is
  evaluated at tolerances `{0,1,2}`, `{0,1}`, and `{0}`, respectively, using
  the same saved generations and attacks.
- `run_three_model_llm_editor_nearest_feasible.slurm`: nine dependent editor tasks,
  one per source-model/bias pair. Qwen3-8B is the common editor while each source
  model retains its own tokenizer and partition.
  Accepted edits are generated once and re-evaluated at the same tolerance sets.
- `submit_nearest_feasible_pipeline.sh`: submits the ECC array and then the editor
  array with an `afterok` dependency.

## MSI submission

```bash
cd ~/EMNLP
mkdir -p logs
python -m unittest tests.test_bucket_compatibility tests.test_three_model_refactor -q
bash msi/submit_nearest_feasible_pipeline.sh
```

The script prints both job IDs. Monitor them with:

```bash
squeue -u "$USER"
sacct -j SOURCE_JOB_ID,EDITOR_JOB_ID --format=JobID,JobName,State,Elapsed,ExitCode
```

## Outputs

```text
outputs/three_model_ecc_soft_sweep_nearest_feasible_v1/<model>/
outputs/editor_seeds_nearest_feasible_v1/<model>/delta<2|5|20>/
outputs/llm_editor_nearest_feasible_v1/<model>/delta<2|5|20>/
outputs/llm_editor_nearest_feasible_v1/<model>/delta<2|5|20>/tolerance_sweep/tolerance_<r>/
```

The seed exporter verifies that every source setting records
`adaptive_invalid_prefix_policy=nearest_feasible` and aborts otherwise.
