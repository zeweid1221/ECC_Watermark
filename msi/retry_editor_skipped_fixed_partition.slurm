#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=16:00:00
#SBATCH -J wm_editor_retry
#SBATCH --array=0-1
#SBATCH -o logs/editor_retry_%A_%a.out
#SBATCH -e logs/editor_retry_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
mkdir -p logs
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

BIAS_VALUES=(5 20)
TOLERANCE_VALUES=(1 0)
TASK_INDEX=${SLURM_ARRAY_TASK_ID:-0}
LOGIT_BIAS=${BIAS_VALUES[$TASK_INDEX]}
TOLERANCE=${TOLERANCE_VALUES[$TASK_INDEX]}

SOURCE_CSV="outputs/editor_seeds/qwen3_delta${LOGIT_BIAS}_256_fixed18/editor_seed.csv"
PARTITION_DIR="outputs/partitions/qwen3-8b-semantic-v1"
BASE_OUTPUT_DIR="outputs/llm_editor_qwen3_delta${LOGIT_BIAS}_source256_fixed18_aggressive_min6_max10"
OUTPUT_DIR="outputs/llm_editor_qwen3_delta${LOGIT_BIAS}_source256_fixed18_aggressive_min6_max10_retry_noop_v2"

if [ ! -f "$SOURCE_CSV" ]; then
  echo "ERROR: missing seed CSV $SOURCE_CSV" >&2
  exit 1
fi
if [ ! -f "$BASE_OUTPUT_DIR/llm_editor_details.csv" ]; then
  echo "ERROR: missing completed first-round details in $BASE_OUTPUT_DIR" >&2
  exit 1
fi
if [ ! -f "$PARTITION_DIR/token_to_bucket.npy" ] || [ ! -f "$PARTITION_DIR/partition_config.json" ]; then
  echo "ERROR: incomplete partition directory $PARTITION_DIR" >&2
  exit 1
fi

python scripts/run_llm_editor_experiment.py \
  --seed-csv "$SOURCE_CSV" \
  --partition-dir "$PARTITION_DIR" \
  --require-semantic-partition \
  --model-backend hf \
  --model-profile qwen3-8b \
  --device cuda \
  --use-4bit \
  --editor-backend hf \
  --question-aware \
  --num-samples 256 \
  --motivation-assignment round_robin \
  --motivations grammar_polish,clarity_improvement,style_softening,claim_distortion,stance_shift,source_spoofing \
  --min-edit-instructions 6 \
  --max-edit-instructions 10 \
  --aggressive-malicious-edits \
  --max-edited-blocks 18 \
  --max-block-edit-rate 1.01 \
  --max-retries 2 \
  --editor-max-new-tokens 768 \
  --decoder-max-edits-per-block 3 \
  --block-len 7 \
  --vt-a 6 \
  --tolerance "$TOLERANCE" \
  --checkpoint-every 10 \
  --resume \
  --resume-from-output-dir "$BASE_OUTPUT_DIR" \
  --retry-skipped \
  --output-dir "$OUTPUT_DIR"
