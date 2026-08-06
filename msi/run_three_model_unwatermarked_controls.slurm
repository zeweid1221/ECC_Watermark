#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --array=0-2
#SBATCH -J wm_unwatermarked
#SBATCH -o logs/unwatermarked_%A_%a.out
#SBATCH -e logs/unwatermarked_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0
export TOKENIZERS_PARALLELISM=false

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
PROMPT_FILE="outputs/three_model_ecc_soft_sweep/${PROFILE}/prompts.txt"
OUTPUT_DIR="outputs/three_model_unwatermarked_controls_v1/${PROFILE}"
QUANT_ARGS=()
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS+=(--use-4bit)
fi

if [ ! -f "$PROMPT_FILE" ]; then
  echo "ERROR: missing matched prompt file: $PROMPT_FILE" >&2
  exit 1
fi

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
  --resume
