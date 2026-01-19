# TCT Models

Training and evaluation code for **Type-Constrained Tokenization (TCT)** language models for structured JSON generation.

This repository contains the accompanying code for the paper:

> **Type-Constrained Tokenization: Enabling Syntax-Free Learning for Structured Generation**
>
> *Submitted to ICML 2026 (anonymous)*

## Overview

This repository contains code for training small GPT-style language models that generate valid JSON documents for specific schemas:

- **Kubernetes** manifests (Deployments, Services, ConfigMaps, etc.)
- **TSConfig** (TypeScript configuration files)
- **ESLint** configuration files

TCT models use schema-aware tokenization that guarantees structurally valid output, compared to standard UTF8-BPE models that require post-hoc constraint enforcement (e.g., XGrammar).

## Quick Start

```bash
# 1. Setup environment and extract data
bash scripts/setup.sh

# 2. Train a model
bash scripts/train.sh kubernetes mini

# 3. Evaluate
bash scripts/eval.sh kubernetes mini
```

## Project Structure

```
tct-models/
├── nanochat/               # Core model code (GPT, optimizers, dataloaders)
├── configs/                # Schema and model configurations
├── scripts/
│   ├── setup.sh            # Environment setup
│   ├── train.sh            # Training launcher
│   ├── train_unified.py    # Training script
│   ├── eval.sh             # Evaluation launcher
│   ├── eval_icml.py        # BPB and generation evaluation
│   └── eval_generation.py  # Generation-only evaluation
├── checkpoints/            # Trained model weights
├── data/                   # Training data (extracted from .tar.xz)
├── bpe-merges/             # BPE merge tables
├── schemas/                # JSON schemas for validation
└── tct-wheels/             # TCT tokenizer wheels
```

## Model Sizes

| Size | d_model | Layers | Heads | Parameters |
|------|---------|--------|-------|------------|
| tiny | 128 | 4 | 4 | ~5M |
| mini | 256 | 6 | 8 | ~15M |
| base | 384 | 8 | 8 | ~35M |
| small | 512 | 10 | 8 | ~50M |
| medium | 768 | 12 | 12 | ~125M |

## Schemas

Each schema has both TCT and UTF8-BPE tokenized datasets:

| Schema | TCT Vocab | UTF8 Vocab | Context |
|--------|-----------|------------|---------|
| kubernetes | 1000 | 1527 | 2048 |
| tsconfig | 258 | 277 | 2048 |
| eslintrc | 500 | 717 | 2048 |

## Training

```bash
# Train specific schema and size
bash scripts/train.sh kubernetes mini

# Train multiple schemas
bash scripts/train.sh kubernetes tsconfig eslintrc mini

# Train both tokenizers (TCT and UTF8)
bash scripts/train.sh kubernetes mini  # runs both by default

# Train only TCT
bash scripts/train.sh kubernetes mini tct

# Resume from checkpoint
bash scripts/train.sh kubernetes mini resume

# Custom epochs
bash scripts/train.sh kubernetes mini --epochs=50
```

## Evaluation

```bash
# Full evaluation (BPB + generation)
bash scripts/eval.sh kubernetes mini

# Quick test with fewer samples
bash scripts/eval.sh kubernetes mini --samples=100 --gen_samples=100
```

## Generation Testing

```bash
# Test generation with trained models
python -m scripts.eval_generation \
    --schema kubernetes \
    --tct_checkpoint checkpoints/kubernetes_tct_mini \
    --utf8_checkpoint checkpoints/kubernetes_utf8_mini \
    --eval_generation \
    --num_samples 10 \
    --save_samples results/samples/
```

## Requirements

- Python 3.12
- PyTorch 2.8+ with CUDA
- uv package manager

Dependencies are managed via `pyproject.toml` and installed with `uv sync`.

## Acknowledgements

The model training code is adapted from [nanochat](https://github.com/karpathy/nanochat) by Andrej Karpathy. We use his clean GPT implementation, Muon optimizer, and training infrastructure as the foundation for TCT model training.

```bibtex
@misc{nanochat,
  author = {Andrej Karpathy},
  title = {nanochat: The best ChatGPT that $100 can buy},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/karpathy/nanochat}
}
```

## License

MIT
