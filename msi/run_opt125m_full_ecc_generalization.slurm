#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH -J wm_opt125_full
#SBATCH -o /users/2/deng0379/EMNLP/logs/opt125_full_%j.out
#SBATCH -e /users/2/deng0379/EMNLP/logs/opt125_full_%j.err

set -euo pipefail
EMNLP_DIR=${SLURM_SUBMIT_DIR:-$HOME/EMNLP}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0

python run_main.py \
  --backend hf \
  --model-name facebook/opt-125m \
  --device cuda \
  --prompt-file prompts.txt \
  --output-dir outputs/rebuttal_opt125m_full_ecc_generalization \
  --schemes ecc \
  --disable-segment-baselines \
  --watermark-modes soft \
  --ecc-logit-bias-values "2,5,20" \
  --ecc-adaptive-modes true,false \
  --prompt-count 256 \
  --target-blocks 18 \
  --max-new-tokens 160 \
  --edit-rates "0.2,0.4,0.6,0.8" \
  --attack-max-edits-per-blocks "1,2,3" \
  --decoder-max-edits-per-block 3 \
  --ecc-tolerance-by-logit-bias "2:2,5:1,20:0"

echo "Saved OPT-125M full ECC generalization sweep to:"
echo "  outputs/rebuttal_opt125m_full_ecc_generalization"
