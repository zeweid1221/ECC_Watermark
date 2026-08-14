#!/bin/bash
set -euo pipefail

EMNLP_DIR=${EMNLP_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
mkdir -p logs outputs/ecc_boundary_eighth_20260813

PARTITION_JOB=$(sbatch --parsable msi/build_three_model_boundary_eighth_partitions.slurm)
ECC_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${PARTITION_JOB}" \
    msi/run_three_model_boundary_eighth_ecc.slurm
)
CLEAN_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${ECC_JOB}" \
    msi/run_three_model_boundary_eighth_unwatermarked.slurm
)
EDITOR_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${ECC_JOB}" \
    msi/run_three_model_boundary_eighth_llm_editor.slurm
)

cat > outputs/ecc_boundary_eighth_20260813/submitted_jobs.txt <<EOF
partition=${PARTITION_JOB}
ecc_adaptive=${ECC_JOB}
unwatermarked=${CLEAN_JOB}
llm_editor=${EDITOR_JOB}
EOF

echo "Boundary partitions: $PARTITION_JOB"
echo "Adaptive ECC:       $ECC_JOB (after partition)"
echo "Clean controls:     $CLEAN_JOB (after ECC)"
echo "LLM-guided edits:   $EDITOR_JOB (after ECC)"
echo "Monitor: squeue -j $PARTITION_JOB,$ECC_JOB,$CLEAN_JOB,$EDITOR_JOB"
