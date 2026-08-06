#!/bin/bash
set -euo pipefail

# Optional first-time MSI environment setup. Run on MSI login node if the
# watermark conda environment does not already exist. This does not submit jobs.

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
else
  echo "conda not found. Install miniconda or use MSI's Python module, then create an equivalent env." >&2
  exit 1
fi

conda create -n watermark python=3.10 -y
conda activate watermark
python -m pip install --upgrade pip
python -m pip install torch transformers accelerate bitsandbytes pandas pyarrow numpy tqdm sentencepiece protobuf
python - <<'PY'
import torch, transformers, pandas
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("transformers", transformers.__version__)
print("pandas", pandas.__version__)
PY
