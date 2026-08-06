# MSI Qwen3 Fixed-Partition Pipeline

This folder contains Slurm helpers for the clean Qwen3 downstream run.

1. `run_source_fixed_partition.slurm`
   Generates 500 LFQA Qwen3 source texts with `outputs/qwen3_fixed_partition_v1`.
   Output: `outputs/lfqa_qwen3_delta5_source500_blocks12_fixed_partition_v1/preview_generations.csv`

2. `run_editor_fixed_partition.slurm`
   Runs LLM-guided edits using the source CSV above and the same fixed partition.
   Output: `outputs/llm_editor_qwen3_fixed_partition_source500_aggressive_max10/llm_editor_details.csv`

3. `run_judge_fixed_partition.slurm`
   Runs judge with `no_warning`, `detector_warning`, and `random_warning`.
   Output: `outputs/malicious_judge_qwen3_fixed_partition_full500_three_conditions/`

4. `submit_pipeline.sh`
   Submits the three jobs with Slurm dependencies: source -> editor -> judge.

Default Slurm resources are `-A liyanxie`, `-p a100-4`, `--gres=gpu:a100:1`.
If A100 queues are long, edit the scripts to use `-p msigpu --gres=gpu:h100:1`
or an available L40S/A40 partition.

Before submitting:

```bash
cd EMNLP
bash msi/setup_env_msi.sh   # only if the conda env does not already exist
bash msi/submit_pipeline.sh
squeue -u $USER
```

The old `lfqa_qwen3_delta5_source500_blocks12_true_tokens` source artifact is
not used because it predates the fixed partition.
