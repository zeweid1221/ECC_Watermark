#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --array=0-2
#SBATCH -J wm_clean_1of8
#SBATCH -o logs/clean_1of8_%A_%a.out
#SBATCH -e logs/clean_1of8_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0
export TOKENIZERS_PARALLELISM=false

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
SOURCE_ROOT=${SOURCE_ROOT:-"outputs/ecc_boundary_eighth_20260813/adaptive_nearest"}
PROMPT_FILE="$SOURCE_ROOT/$PROFILE/prompts.txt"
OUTPUT_ROOT=${OUTPUT_ROOT:-"outputs/ecc_boundary_eighth_20260813/unwatermarked_controls"}
OUTPUT_DIR="$OUTPUT_ROOT/$PROFILE"
QUANT_ARGS=()
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS+=(--use-4bit)
fi

test -f "$PROMPT_FILE"

python scripts/generate_unwatermarked_controls.py \
  --backend hf \
  --model-profile "$PROFILE" \
  --device cuda \
  "${QUANT_ARGS[@]}" \
  --prompt-file "$PROMPT_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --num-samples 256 \
  --target-new-tokens 144 \
  --max-prompt-tokens 256 \
  --sampling sample \
  --temperature 0.75 \
  --top-k 40 \
  --top-p 0.9 \
  --repetition-penalty 1.2 \
  --english-token-filter \
  --seed 2043 \
  --compute-ppl \
  --no-resume
