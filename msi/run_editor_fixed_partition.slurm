#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=24:00:00
#SBATCH -J wm_editor_qwen3
#SBATCH --array=0-1
#SBATCH -o logs/editor_%A_%a.out
#SBATCH -e logs/editor_%A_%a.err

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
SETTING_KEY="ecc_soft_adaptive_bias${BIAS_LABEL}"

DETAILED_RESULTS=${DETAILED_RESULTS:-"outputs/three_model_ecc_soft_sweep/qwen3-8b/detailed_results.json"}
SOURCE_CSV=${SOURCE_CSV:-"outputs/editor_seeds/qwen3_delta${BIAS_LABEL}_256_fixed18/editor_seed.csv"}
PARTITION_DIR=${PARTITION_DIR:-"outputs/partitions/qwen3-8b-semantic-v1"}
OUTPUT_DIR=${OUTPUT_DIR:-"outputs/llm_editor_qwen3_delta${BIAS_LABEL}_source256_fixed18_aggressive_min6_max10"}
NUM_SAMPLES=${NUM_SAMPLES:-256}
if [ ! -f "$SOURCE_CSV" ]; then
  if [ ! -f "$DETAILED_RESULTS" ]; then
    echo "ERROR: missing both $SOURCE_CSV and $DETAILED_RESULTS." >&2
    exit 1
  fi
  python scripts/export_editor_seed_from_detailed_results.py \
    --detailed-results "$DETAILED_RESULTS" \
    --output-csv "$SOURCE_CSV" \
    --setting-key "$SETTING_KEY" \
    --target-blocks 18
fi
if [ ! -f "$PARTITION_DIR/token_to_bucket.npy" ] || [ ! -f "$PARTITION_DIR/partition_config.json" ]; then
  echo "ERROR: incomplete partition directory $PARTITION_DIR." >&2
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
  --num-samples "$NUM_SAMPLES" \
  --motivation-assignment round_robin \
  --motivations grammar_polish,clarity_improvement,style_softening,claim_distortion,stance_shift,source_spoofing \
  --min-edit-instructions 6 \
  --max-edit-instructions 10 \
  --aggressive-malicious-edits \
  --max-edited-blocks 18 \
  --max-block-edit-rate 1.01 \
  --max-retries 1 \
  --editor-max-new-tokens 768 \
  --decoder-max-edits-per-block 3 \
  --block-len 7 \
  --vt-a 6 \
  --tolerance "$TOLERANCE" \
  --checkpoint-every 10 \
  --resume \
  --output-dir "$OUTPUT_DIR"
