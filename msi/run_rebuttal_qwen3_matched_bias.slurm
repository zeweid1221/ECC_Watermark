#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH -J wm_rebuttal_bias
#SBATCH -o /users/2/deng0379/EMNLP/logs/rebuttal_bias_%j.out
#SBATCH -e /users/2/deng0379/EMNLP/logs/rebuttal_bias_%j.err

set -euo pipefail
EMNLP_DIR=${SLURM_SUBMIT_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

COMMON_ARGS=(
  --backend hf
  --model-name Qwen/Qwen3-8B
  --device cuda
  --use-4bit
  --prompt-file rebuttal/qwen3_matched_bias_prompts_2.txt
  --partition-dir outputs/qwen3_fixed_partition_v1
  --num-samples 2
  --prompt-style qa
  --use-chat-template
  --target-blocks 12
  --max-new-tokens 96
  --stop-after closed_blocks
  --watermark-mode soft
  --adaptive true
  --sampling sample
  --temperature 0.75
  --top-k 40
  --top-p 0.9
  --repetition-penalty 1.2
  --english-token-filter
  --seed 20260607
  --print-samples 2
)

python scripts/preview_watermarked_generation_quality.py \
  "${COMMON_ARGS[@]}" \
  --logit-bias 2 \
  --include-unwatermarked \
  --output-dir outputs/rebuttal_qwen3_matched_bias_v2_delta2

python scripts/preview_watermarked_generation_quality.py \
  "${COMMON_ARGS[@]}" \
  --logit-bias 5 \
  --output-dir outputs/rebuttal_qwen3_matched_bias_v2_delta5

python scripts/preview_watermarked_generation_quality.py \
  "${COMMON_ARGS[@]}" \
  --logit-bias 20 \
  --output-dir outputs/rebuttal_qwen3_matched_bias_v2_delta20

echo "Saved matched rebuttal generations under:"
echo "  outputs/rebuttal_qwen3_matched_bias_v2_delta2"
echo "  outputs/rebuttal_qwen3_matched_bias_v2_delta5"
echo "  outputs/rebuttal_qwen3_matched_bias_v2_delta20"
