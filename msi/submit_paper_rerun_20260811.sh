#!/bin/bash
set -euo pipefail

EMNLP_DIR=${EMNLP_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
mkdir -p logs outputs/paper_rerun_20260811

SOURCE_JOB=$(sbatch --parsable msi/run_paper_ecc_nearest_20260811.slurm)
QUALITY_JOB=$(sbatch --parsable msi/run_paper_ecc_nonadaptive_quality_20260811.slurm)
CLEAN_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${SOURCE_JOB}" \
    msi/run_paper_unwatermarked_20260811.slurm
)
EDITOR_JOB=$(
  sbatch --parsable \
    --dependency="afterok:${SOURCE_JOB}" \
    msi/run_paper_llm_editor_nearest_20260811.slurm
)

cat > outputs/paper_rerun_20260811/submitted_jobs.txt <<EOF
source_adaptive=${SOURCE_JOB}
quality_nonadaptive=${QUALITY_JOB}
unwatermarked=${CLEAN_JOB}
llm_editor=${EDITOR_JOB}
EOF

echo "Adaptive ECC + synthetic edits: $SOURCE_JOB"
echo "Non-adaptive PPL ablation:       $QUALITY_JOB"
echo "Unwatermarked controls:          $CLEAN_JOB (after source)"
echo "LLM-guided edits:                $EDITOR_JOB (after source)"
echo "Monitor: squeue -j $SOURCE_JOB,$QUALITY_JOB,$CLEAN_JOB,$EDITOR_JOB"
