#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH -J wm_source_qwen3
#SBATCH -o logs/source_%j.out
#SBATCH -e logs/source_%j.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
mkdir -p logs
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

python scripts/preview_watermarked_generation_quality.py \
  --backend hf \
  --model-profile qwen3-8b \
  --device cuda \
  --use-4bit \
  --prompt-file outputs/text_quality_lfqa_screen/lfqa_prompts_500.txt \
  --partition-dir outputs/partitions/qwen3-8b-semantic-v1 \
  --require-semantic-partition \
  --output-dir outputs/lfqa_qwen3_delta5_source500_blocks12_semantic_partition_v2 \
  --num-samples 500 \
  --prompt-style qa \
  --use-chat-template \
  --target-blocks 12 \
  --max-new-tokens 160 \
  --stop-after closed_blocks \
  --watermark-mode soft \
  --logit-bias 5 \
  --adaptive true \
  --temperature 0.75 \
  --top-k 40 \
  --top-p 0.9 \
  --repetition-penalty 1.2 \
  --seed 20260607 \
  --print-samples 0
