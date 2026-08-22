#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
#SBATCH -J wm_sync_lfqa
#SBATCH -o logs/sync_lfqa_%j.out
#SBATCH -e logs/sync_lfqa_%j.err

set -euo pipefail

EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"

export PYTHONHASHSEED=0
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false

PROFILE=${MODEL_PROFILE:-qwen3-8b}
PROMPT_FILE=${PROMPT_FILE:-"outputs/text_quality_lfqa_screen/lfqa_prompts_500.txt"}
RUN_TAG=${RUN_TAG:-"qwen3_sync_ecc_lfqa_256_v1"}
OUTPUT_DIR=${OUTPUT_DIR:-"outputs/sync_ecc_lfqa_baseline/$RUN_TAG"}

test -s "$PROMPT_FILE"
mkdir -p logs "$OUTPUT_DIR"

python -m unittest tests.test_sync_ecc_baseline -v

python scripts/run_sync_ecc_lfqa_baseline.py \
  --backend hf \
  --model-profile "$PROFILE" \
  --device cuda \
  --use-4bit \
  --prompt-file "$PROMPT_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --num-samples 256 \
  --logit-bias-values "2,5,20" \
  --watermark-mode soft \
  --target-blocks 18 \
  --block-len 7 \
  --sigma-size 4 \
  --vt-a 4 \
  --max-new-tokens 160 \
  --sampling sample \
  --temperature 0.75 \
  --top-k 40 \
  --top-p 0.9 \
  --repetition-penalty 1.2 \
  --edit-rates "0.2,0.4,0.6,0.8" \
  --attack-max-edits-per-blocks "1,2,3" \
  --attack-types "insert,delete,substitute" \
  --edit-count-mode uniform_1_to_k \
  --strict-interior-insertions \
  --candidate-tolerance 1 \
  --save-parquet

python scripts/validate_sync_ecc_lfqa_results.py \
  --result-dir "$OUTPUT_DIR" \
  --expected-samples 256

echo "SYNC_ECC_LFQA_RUN_COMPLETE=$OUTPUT_DIR"
