#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=12:00:00
#SBATCH --array=0-8
#SBATCH -J wm_edit_1of8
#SBATCH -o logs/edit_1of8_%A_%a.out
#SBATCH -e logs/edit_1of8_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
BIAS_VALUES=(2 5 20)
DEFAULT_TOLERANCES=(2 1 0)
TASK_INDEX=${SLURM_ARRAY_TASK_ID:-0}
MODEL_INDEX=$((TASK_INDEX / 3))
BIAS_INDEX=$((TASK_INDEX % 3))
PROFILE=${PROFILES[$MODEL_INDEX]}
LOGIT_BIAS=${BIAS_VALUES[$BIAS_INDEX]}
TOLERANCE=${DEFAULT_TOLERANCES[$BIAS_INDEX]}
BIAS_LABEL=${LOGIT_BIAS//./p}
SETTING_KEY="ecc_soft_adaptive_bias${BIAS_LABEL}"

SOURCE_ROOT=${SOURCE_ROOT:-"outputs/ecc_boundary_eighth_20260813/adaptive_nearest"}
SEED_ROOT=${SEED_ROOT:-"outputs/ecc_boundary_eighth_20260813/editor_seeds"}
OUTPUT_ROOT=${OUTPUT_ROOT:-"outputs/ecc_boundary_eighth_20260813/llm_editor"}
DETAILED_RESULTS="$SOURCE_ROOT/$PROFILE/detailed_results.json"
SOURCE_CSV="$SEED_ROOT/$PROFILE/delta${BIAS_LABEL}/editor_seed.csv"
PARTITION_DIR="outputs/partitions/${PROFILE}-boundary-eighth-semantic-v2"
OUTPUT_DIR="$OUTPUT_ROOT/$PROFILE/delta${BIAS_LABEL}"
EDITOR_MODEL=${EDITOR_MODEL:-"Qwen/Qwen3-8B"}

test -f "$DETAILED_RESULTS"
test -f "$PARTITION_DIR/token_to_bucket.npy"

python scripts/export_editor_seed_from_detailed_results.py \
  --detailed-results "$DETAILED_RESULTS" \
  --output-csv "$SOURCE_CSV" \
  --setting-key "$SETTING_KEY" \
  --target-blocks 18 \
  --expected-invalid-prefix-policy nearest_feasible

python scripts/run_llm_editor_experiment.py \
  --seed-csv "$SOURCE_CSV" \
  --partition-dir "$PARTITION_DIR" \
  --require-semantic-partition \
  --model-backend hf \
  --model-profile "$PROFILE" \
  --device cuda \
  --use-4bit \
  --editor-backend hf \
  --editor-model "$EDITOR_MODEL" \
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
  --output-dir "$OUTPUT_DIR"

case "$LOGIT_BIAS" in
  2) EVAL_TOLERANCES=(0 1 2) ;;
  5) EVAL_TOLERANCES=(0 1) ;;
  20) EVAL_TOLERANCES=(0) ;;
  *) echo "ERROR: unsupported logit bias $LOGIT_BIAS" >&2; exit 1 ;;
esac

for EVAL_TOLERANCE in "${EVAL_TOLERANCES[@]}"; do
  python scripts/recompute_llm_editor_evaluation.py \
    --source-dir "$OUTPUT_DIR" \
    --output-dir "$OUTPUT_DIR/tolerance_sweep/tolerance_${EVAL_TOLERANCE}" \
    --tolerance "$EVAL_TOLERANCE"
done
