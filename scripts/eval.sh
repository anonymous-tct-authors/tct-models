#!/bin/bash -l
# Unified Evaluation Script for TCT vs UTF8+XGrammar
# Works with all schemas: kubernetes, tsconfig, eslintrc
#
# Usage:
#   bash scripts/eval.sh kubernetes              # Evaluate kubernetes (auto-detect size)
#   bash scripts/eval.sh kubernetes mini         # Evaluate specific size
#   bash scripts/eval.sh kubernetes --samples=1000  # Custom sample count

set -e

# =============================================================================
# Parse arguments
# =============================================================================

SCHEMA=""
SIZE=""
NUM_SAMPLES=""
NUM_GEN_SAMPLES=""
EXTRA_ARGS=""

for arg in "$@"; do
    case $arg in
        kubernetes|tsconfig|eslintrc) SCHEMA="$arg" ;;
        tiny|mini|base|small|small-wide|medium|large) SIZE="$arg" ;;
        --samples=*) NUM_SAMPLES="${arg#--samples=}" ;;
        --gen_samples=*) NUM_GEN_SAMPLES="${arg#--gen_samples=}" ;;
        --bpb_only|--generation_only|--skip_raw_generation) EXTRA_ARGS="$EXTRA_ARGS $arg" ;;
    esac
done

if [ -z "$SCHEMA" ]; then
    echo "Usage: bash scripts/eval.sh <schema> [size] [options]"
    echo ""
    echo "Schemas: kubernetes, tsconfig, eslintrc"
    echo "Sizes: tiny, mini, base, small, small-wide, medium, large (auto-detect if omitted)"
    echo "Options:"
    echo "  --samples=N       BPB samples (default: full validation set)"
    echo "  --gen_samples=N   Generation samples (default: 10000)"
    echo ""
    echo "Examples:"
    echo "  bash scripts/eval.sh kubernetes              # Auto-detect size, full validation"
    echo "  bash scripts/eval.sh kubernetes mini         # Specific size"
    echo "  bash scripts/eval.sh kubernetes --samples=100 --gen_samples=100  # Quick test"
    exit 1
fi

# =============================================================================
# Paths (all within tct-models folder)
# =============================================================================

CODE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$CODE_DIR/data"
CHECKPOINT_DIR="$CODE_DIR/checkpoints"
RESULTS_DIR="$CODE_DIR/results"

mkdir -p "$RESULTS_DIR"

# =============================================================================
# Find checkpoints
# =============================================================================

# Auto-detect size if not specified
if [ -z "$SIZE" ]; then
    # Try sizes in order of preference
    for try_size in mini small base medium large tiny; do
        tct_try="${CHECKPOINT_DIR}/${SCHEMA}_tct_${try_size}"
        utf8_try="${CHECKPOINT_DIR}/${SCHEMA}_utf8_${try_size}"
        if [ -d "$tct_try" ] && [ -d "$utf8_try" ]; then
            SIZE="$try_size"
            break
        fi
    done
    if [ -z "$SIZE" ]; then
        echo "ERROR: No matching checkpoints found for schema '$SCHEMA'"
        echo "Looking in: $CHECKPOINT_DIR"
        echo ""
        echo "Available checkpoints:"
        ls -d "$CHECKPOINT_DIR"/${SCHEMA}_* 2>/dev/null || echo "  (none)"
        exit 1
    fi
    echo "Auto-detected size: $SIZE"
fi

# Build checkpoint paths
TCT_CHECKPOINT="${CHECKPOINT_DIR}/${SCHEMA}_tct_${SIZE}"
UTF8_CHECKPOINT="${CHECKPOINT_DIR}/${SCHEMA}_utf8_${SIZE}"

# Validate checkpoints exist
if [ ! -d "$TCT_CHECKPOINT" ]; then
    echo "ERROR: TCT checkpoint not found: $TCT_CHECKPOINT"
    exit 1
fi
if [ ! -d "$UTF8_CHECKPOINT" ]; then
    echo "ERROR: UTF8 checkpoint not found: $UTF8_CHECKPOINT"
    exit 1
fi

# =============================================================================
# Run evaluation
# =============================================================================

# Build output filename
OUTPUT_FILE="$RESULTS_DIR/${SCHEMA}_${SIZE}_eval.json"

echo "============================================================"
echo "TCT vs UTF8+XGrammar Evaluation"
echo "============================================================"
echo "Date:       $(date)"
echo "Schema:     $SCHEMA"
echo "Size:       $SIZE"
echo "TCT:        $TCT_CHECKPOINT"
echo "UTF8:       $UTF8_CHECKPOINT"
echo "Data:       $DATA_DIR"
echo "BPB:        ${NUM_SAMPLES:-all} samples"
echo "Generation: ${NUM_GEN_SAMPLES:-10000} samples"
echo "Output:     $OUTPUT_FILE"
echo "============================================================"
echo

cd "$CODE_DIR"

# Build command with optional arguments
CMD="python -m scripts.eval_icml --schema $SCHEMA --tct_checkpoint $TCT_CHECKPOINT --utf8_checkpoint $UTF8_CHECKPOINT"
[ -n "$NUM_SAMPLES" ] && CMD="$CMD --num_samples $NUM_SAMPLES"
[ -n "$NUM_GEN_SAMPLES" ] && CMD="$CMD --num_gen_samples $NUM_GEN_SAMPLES"
[ -n "$EXTRA_ARGS" ] && CMD="$CMD $EXTRA_ARGS"
CMD="$CMD --output $OUTPUT_FILE --latex"

eval $CMD

echo ""
echo "============================================================"
echo "Results saved to: $OUTPUT_FILE"
echo "============================================================"
