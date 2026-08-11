#!/bin/bash -l
#SBATCH -A liyanxie
#SBATCH -p a100-4
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --array=0-2
#SBATCH -J wm_bucket_mass
#SBATCH -o logs/bucket_mass_%A_%a.out
#SBATCH -e logs/bucket_mass_%A_%a.err

set -euo pipefail
EMNLP_DIR=${EMNLP_DIR:-${SLURM_SUBMIT_DIR:-$HOME/EMNLP}}
cd "$EMNLP_DIR"
source "$EMNLP_DIR/msi/activate_env.sh"

export PYTHONHASHSEED=0
export HF_HUB_DISABLE_PROGRESS_BARS=1

PROFILES=(qwen3-8b mistral-7b-instruct-v0.3 opt-125m)
MODEL_NAMES=(Qwen/Qwen3-8B mistralai/Mistral-7B-Instruct-v0.3 facebook/opt-125m)
PROFILE=${PROFILES[$SLURM_ARRAY_TASK_ID]}
MODEL_NAME=${MODEL_NAMES[$SLURM_ARRAY_TASK_ID]}

SOURCE_ROOT=${SOURCE_ROOT:-outputs/three_model_ecc_soft_sweep}
PARTITION_ROOT=${PARTITION_ROOT:-outputs/partitions}
OUTPUT_ROOT=${OUTPUT_ROOT:-outputs/bucket_compatibility_three_model_20260808_v2}
INVALID_PREFIX_POLICY=${INVALID_PREFIX_POLICY:-nearest_feasible}
DETAILED_RESULTS="$SOURCE_ROOT/$PROFILE/detailed_results.json"
PARTITION_DIR="$PARTITION_ROOT/$PROFILE-semantic-v1"
OUTPUT_DIR="$OUTPUT_ROOT/$PROFILE"

case "$INVALID_PREFIX_POLICY" in
  nearest_feasible|legacy_unconstrained) ;;
  *)
    echo "ERROR: INVALID_PREFIX_POLICY must be nearest_feasible or legacy_unconstrained; got $INVALID_PREFIX_POLICY" >&2
    exit 2
    ;;
esac

if [ ! -f "$DETAILED_RESULTS" ]; then
  echo "ERROR: missing $DETAILED_RESULTS" >&2
  exit 1
fi
if [ ! -f "$PARTITION_DIR/token_to_bucket.npy" ]; then
  echo "ERROR: missing $PARTITION_DIR/token_to_bucket.npy" >&2
  exit 1
fi

QUANT_ARGS=(--no-use-4bit)
if [ "$PROFILE" != "opt-125m" ]; then
  QUANT_ARGS=(--use-4bit)
fi

python scripts/analyze_bucket_compatibility.py \
  --detailed-results "$DETAILED_RESULTS" \
  --partition-dir "$PARTITION_DIR" \
  --model-name "$MODEL_NAME" \
  --model-profile "$PROFILE" \
  --output-dir "$OUTPUT_DIR" \
  --device cuda \
  "${QUANT_ARGS[@]}" \
  --no-local-files-only \
  --invalid-prefix-policy "$INVALID_PREFIX_POLICY" \
  --checkpoint-every 16
