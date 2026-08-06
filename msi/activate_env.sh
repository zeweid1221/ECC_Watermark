#!/bin/bash -l

# Shared MSI environment activation for the Qwen3 fixed-partition runs.
# Edit this file if your MSI conda path or environment name is different.
#
# This file is sourced by both Slurm launchers and interactive shells. Do not
# enable errexit/nounset/pipefail here because those options would leak into the
# caller; each Slurm launcher sets its own strict shell options.

_watermark_activate_fail() {
  echo "ERROR: $*" >&2
  return 1
}

# MSI exposes the Anaconda installation through a module rather than a
# user-local miniconda installation. Load it when a fresh login shell does not
# already provide conda.
if ! command -v conda >/dev/null 2>&1 && command -v module >/dev/null 2>&1; then
  module load python/3.10.9_anaconda2023.03_libmamba ||
    _watermark_activate_fail "failed to load MSI's Anaconda Python module" ||
    return 1
fi

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
else
  _watermark_activate_fail \
    "conda not found after loading the MSI Python module" ||
    return 1
fi

conda activate watermark ||
  _watermark_activate_fail "could not activate conda environment 'watermark'" ||
  return 1

export PYTHONDONTWRITEBYTECODE=1
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}
export HF_HOME=${HF_HOME:-$HOME/.cache/huggingface}

python - <<'PY'
import sys
print("python", sys.executable)
try:
    import torch
    print("torch", torch.__version__, "cuda", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("gpu", torch.cuda.get_device_name(0))
except Exception as exc:
    print("torch_check_failed", repr(exc))
PY
