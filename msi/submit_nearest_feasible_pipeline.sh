#!/bin/bash
set -euo pipefail

EMNLP_DIR=${EMNLP_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
mkdir -p logs

SOURCE_JOB=$(sbatch --parsable msi/run_three_model_ecc_nearest_feasible.slurm)
EDITOR_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${SOURCE_JOB}" \
    msi/run_three_model_llm_editor_nearest_feasible.slurm
)

echo "Nearest-feasible ECC sweep job: $SOURCE_JOB"
echo "Dependent LLM-editor array job: $EDITOR_JOB"
echo "Monitor with: squeue -j $SOURCE_JOB,$EDITOR_JOB"
