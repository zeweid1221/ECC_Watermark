#!/bin/bash
set -euo pipefail

# Submit source -> editor -> judge as dependent Slurm jobs.
# Run from the EMNLP directory after unpacking the bundle on MSI:
#   bash msi/submit_pipeline.sh

jid_source=$(sbatch --parsable msi/run_source_fixed_partition.slurm)
echo "submitted source: $jid_source"

jid_editor=$(sbatch --parsable --dependency=afterok:${jid_source} msi/run_editor_fixed_partition.slurm)
echo "submitted editor: $jid_editor"

jid_judge=$(sbatch --parsable --dependency=afterok:${jid_editor} msi/run_judge_fixed_partition.slurm)
echo "submitted judge: $jid_judge"

echo "Monitor with: squeue -u $USER"
echo "Cancel all with: scancel $jid_source $jid_editor $jid_judge"
