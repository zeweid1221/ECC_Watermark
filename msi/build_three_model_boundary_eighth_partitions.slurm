#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --array=0-2
#SBATCH -J wm_part_1of8
#SBATCH -o logs/part_1of8_%A_%a.out
#SBATCH -e logs/part_1of8_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"
export PYTHONHASHSEED=0
export HF_HUB_DISABLE_PROGRESS_BARS=1
export TOKENIZERS_PARALLELISM=false

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
PROMPT_FILE=${PROMPT_FILE:-"outputs/text_quality_lfqa_screen/lfqa_prompts_500.txt"}
OUTPUT_DIR="outputs/partitions/${PROFILE}-boundary-eighth-semantic-v2"
QUANT_ARGS=()
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS+=(--use-4bit)
fi

test -f "$PROMPT_FILE"

python scripts/build_model_partition.py \
  --model-profile "$PROFILE" \
  --backend hf \
  --device cuda \
  "${QUANT_ARGS[@]}" \
  --prompt-file "$PROMPT_FILE" \
  --output-dir "$OUTPUT_DIR" \
  --boundary-vocab-fraction 0.125 \
  --block-len 7 \
  --vt-a 6

python - "$OUTPUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
summary = json.loads((root / "bucket_summary.json").read_text())
eligible = int(summary["eligible_vocab_size"])
expected = round(eligible / 8)
assert int(summary["num_bucket2"]) == expected
assert abs(int(summary["num_bucket0"]) - int(summary["num_bucket1"])) <= 1
assert summary["boundary_allocation_strategy"] == "eligible_vocab_fraction"
print(f"validated {root}: payload=({summary['num_bucket0']}, {summary['num_bucket1']}), boundary={expected}")
PY
