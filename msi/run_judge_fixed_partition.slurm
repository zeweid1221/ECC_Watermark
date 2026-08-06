#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH -J wm_judge_qwen3
#SBATCH --array=0-1
#SBATCH -o logs/judge_%A_%a.out
#SBATCH -e logs/judge_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
mkdir -p logs
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

BIAS_VALUES=(5 20)
TOLERANCE_VALUES=(1 0)
TASK_INDEX=${SLURM_ARRAY_TASK_ID:-0}
LOGIT_BIAS=${LOGIT_BIAS:-${BIAS_VALUES[$TASK_INDEX]}}
TOLERANCE=${TOLERANCE:-${TOLERANCE_VALUES[$TASK_INDEX]}}
BIAS_LABEL=${LOGIT_BIAS//./p}

DETAILS_CSV=${DETAILS_CSV:-"outputs/llm_editor_qwen3_delta${BIAS_LABEL}_source256_fixed18_aggressive_min6_max10/llm_editor_details.csv"}
SOURCE_CSV=${SOURCE_CSV:-"outputs/editor_seeds/qwen3_delta${BIAS_LABEL}_256_fixed18/editor_seed.csv"}
OUTPUT_DIR=${OUTPUT_DIR:-"outputs/malicious_judge_qwen3_delta${BIAS_LABEL}_source256_fixed18_three_conditions"}
if [ ! -f "$DETAILS_CSV" ]; then
  echo "ERROR: missing $DETAILS_CSV. Run run_editor_fixed_partition.slurm first." >&2
  exit 1
fi

python scripts/run_llm_malicious_judge.py \
  --details-csv "$DETAILS_CSV" \
  --source-csv "$SOURCE_CSV" \
  --question-column prompt \
  --judge-backend hf \
  --judge-model Qwen/Qwen3-8B \
  --device cuda \
  --use-4bit \
  --conditions no_warning,detector_warning,random_warning \
  --max-new-tokens 256 \
  --max-prompt-tokens 256 \
  --only-used true \
  --random-seed 1234 \
  --warning-metadata-source recompute_final_text \
  --source-backend hf \
  --source-model-profile qwen3-8b \
  --partition-dir outputs/partitions/qwen3-8b-semantic-v1 \
  --require-semantic-partition \
  --block-len 7 \
  --vt-a 6 \
  --decoder-max-edits-per-block 3 \
  --tolerance "$TOLERANCE" \
  --output-dir "$OUTPUT_DIR"
