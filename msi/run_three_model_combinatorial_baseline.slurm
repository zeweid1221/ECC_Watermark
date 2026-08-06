#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=16:00:00
#SBATCH --array=0-2
#SBATCH -J wm_combinatorial
#SBATCH -o /users/2/deng0379/EMNLP/logs/combinatorial_%A_%a.out
#SBATCH -e /users/2/deng0379/EMNLP/logs/combinatorial_%A_%a.err

set -euo pipefail

EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
PROMPT_FILE=${PROMPT_FILE:-"outputs/text_quality_lfqa_screen/lfqa_prompts_500.txt"}
OUTPUT_ROOT=${OUTPUT_ROOT:-"outputs/three_model_combinatorial_baseline"}
OUTPUT_DIR="$OUTPUT_ROOT/$PROFILE"

QUANT_ARGS=()
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS+=(--use-4bit)
fi

python scripts/run_combinatorial_baseline.py \
  --backend hf \
  --model-profile "$PROFILE" \
  --device cuda \
  "${QUANT_ARGS[@]}" \
  --prompt-file "$PROMPT_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --num-samples 256 \
  --patterns "AB,ACADBCBD" \
  --logit-bias-values "2,5,20,50" \
  --target-blocks 18 \
  --evaluation-block-len 8 \
  --max-new-tokens 160 \
  --sampling sample \
  --temperature 0.75 \
  --top-k 40 \
  --top-p 0.9 \
  --repetition-penalty 1.2 \
  --edit-rates "0.2,0.4,0.6,0.8" \
  --attack-max-edits-per-blocks "1,2,3" \
  --edit-count-mode uniform_1_to_k \
  --target-clean-far 0.1
