#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --array=0-2
#SBATCH -J wm_partition
#SBATCH -o logs/partition_%A_%a.out
#SBATCH -e logs/partition_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
PROMPT_FILE=${PROMPT_FILE:-"outputs/text_quality_lfqa_screen/lfqa_prompts_500.txt"}
OUTPUT_DIR="outputs/partitions/${PROFILE}-semantic-v1"
QUANT_ARGS=()
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS+=(--use-4bit)
fi

python scripts/build_model_partition.py \
  --model-profile "$PROFILE" \
  --backend hf \
  --device cuda \
  "${QUANT_ARGS[@]}" \
  --prompt-file "$PROMPT_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --target-boundary-size 150 \
  --block-len 7 \
  --vt-a 6
