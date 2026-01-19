#!/bin/bash
# Local Setup Script for TCT Experiments
#
# Usage:
#   bash scripts/setup.sh

set -e

echo "============================================================"
echo "TCT Experiment Setup"
echo "============================================================"
echo "Date: $(date)"
echo

# =============================================================================
# Set paths (everything inside tct-models folder)
# =============================================================================

CODE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$CODE_DIR/data"
VENV_DIR="$CODE_DIR/.venv"

echo "Code dir:  $CODE_DIR"
echo "Data dir:  $DATA_DIR"
echo "Venv dir:  $VENV_DIR"
echo

# =============================================================================
# Setup Python environment with uv
# =============================================================================

echo "[1/3] Setting up Python environment..."

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "uv version: $(uv --version)"

cd "$CODE_DIR"
uv sync
echo "Done."

# =============================================================================
# Setup data directories and extract archives
# =============================================================================

echo "[2/3] Setting up data..."
mkdir -p "$DATA_DIR"
mkdir -p "$CODE_DIR/checkpoints"
mkdir -p "$CODE_DIR/results"

# Required datasets (must match schema_configs.py)
DATASETS="tsconfig-tct-base tsconfig-utf8-base-matched eslintrc-tct-bpe-500 eslintrc-utf8-bpe-500 kubernetes-tct-bpe-1k kubernetes-utf8-bpe-1k"

extract_dataset() {
    local name="$1"
    local archive="$CODE_DIR/data/${name}.tar.xz"
    local target="$DATA_DIR/$name"

    if [ ! -f "$archive" ]; then
        echo "  [SKIP] $name (archive not found)"
        return 0
    fi

    if [ -d "$target" ] && [ -f "$target/all.jsonl" ]; then
        echo "  [OK] $name (already extracted)"
        return 0
    fi

    echo "  [>>] $name (extracting...)"
    mkdir -p "$target"
    tar --no-same-owner -xJf "$archive" -C "$DATA_DIR"
    echo "       Done: $(du -sh "$target" | cut -f1)"
}

echo "Extracting datasets to $DATA_DIR..."
for dataset in $DATASETS; do
    extract_dataset "$dataset"
done
echo "Done."

# =============================================================================
# Verification
# =============================================================================

echo "[3/3] Verifying installation..."
echo
echo "============================================================"
echo "Setup Verification"
echo "============================================================"

# Use uv run for verification (no manual venv activation needed)
echo "Python:   $(uv run python --version)"
echo "PyTorch:  $(uv run python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'NOT INSTALLED')"
echo "CUDA:     $(uv run python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'N/A')"
echo "GPU:      $(uv run python -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")' 2>/dev/null || echo 'N/A')"
echo

# Check datasets
echo "Datasets:"
for dir in $DATASETS; do
    if [ -d "$DATA_DIR/$dir" ] && [ -f "$DATA_DIR/$dir/all.jsonl" ]; then
        echo "  [OK] $dir"
    else
        echo "  [--] $dir"
    fi
done
echo

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo
echo "To activate environment:"
echo "  source $VENV_DIR/bin/activate"
echo
echo "To run training:"
echo "  bash scripts/train.sh kubernetes mini"
echo
echo "To run evaluation:"
echo "  bash scripts/eval.sh kubernetes mini"
echo
