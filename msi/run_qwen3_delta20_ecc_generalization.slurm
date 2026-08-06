#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH -J wm_qwen3_d20
#SBATCH -o /users/2/deng0379/EMNLP/logs/qwen3_d20_%j.out
#SBATCH -e /users/2/deng0379/EMNLP/logs/qwen3_d20_%j.err

set -euo pipefail
EMNLP_DIR=${SLURM_SUBMIT_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

python run_main.py \
  --backend hf \
  --model-name Qwen/Qwen3-8B \
  --device cuda \
  --use-4bit \
  --prompt-file prompts.txt \
  --partition-dir outputs/qwen3_fixed_partition_v1 \
  --output-dir outputs/rebuttal_qwen3_delta20_ecc_generalization \
  --schemes ecc \
  --disable-segment-baselines \
  --watermark-modes soft \
  --ecc-logit-bias-values "20" \
  --ecc-adaptive-modes true \
  --prompt-count 256 \
  --target-blocks 18 \
  --max-new-tokens 160 \
  --edit-rates "0.2,0.4,0.6,0.8" \
  --attack-max-edits-per-blocks "1,2,3" \
  --decoder-max-edits-per-block 3 \
  --ecc-tolerance-by-logit-bias "20:0"

echo "Saved Qwen3 delta=20 ECC generalization run to:"
echo "  outputs/rebuttal_qwen3_delta20_ecc_generalization"
