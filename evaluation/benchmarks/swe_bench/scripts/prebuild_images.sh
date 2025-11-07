#!/usr/bin/env bash
set -eo pipefail

# Pre-build OpenHands runtime images for SWE-bench evaluation
#
# This script builds all OpenHands runtime wrapper images on top of SWE-bench base images
# and pushes them to a Docker registry. This significantly speeds up subsequent evaluations
# by avoiding the need to rebuild images for each instance.
#
# Usage:
#   ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
#       <dataset> <split> <num_workers> [eval_limit]
#
# Example:
#   # Build all images from SWE-bench_Verified
#   ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
#       princeton-nlp/SWE-bench_Verified test 4
#
#   # Build first 10 images for testing
#   ./evaluation/benchmarks/swe_bench/scripts/prebuild_images.sh \
#       princeton-nlp/SWE-bench_Verified test 2 10

DATASET=${1:-"princeton-nlp/SWE-bench_Verified"}
SPLIT=${2:-"test"}
NUM_WORKERS=${3:-1}
EVAL_LIMIT=$4

echo "=========================================="
echo "SWE-bench Image Pre-build Script"
echo "=========================================="
echo "Dataset: $DATASET"
echo "Split: $SPLIT"
echo "Num Workers: $NUM_WORKERS"
if [ -n "$EVAL_LIMIT" ]; then
  echo "Eval Limit: $EVAL_LIMIT"
fi
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Set Docker registry (can be overridden by environment variable)
if [ -z "$OH_RUNTIME_RUNTIME_IMAGE_REPO" ]; then
  OH_RUNTIME_RUNTIME_IMAGE_REPO="ghcr.io/openhands/runtime"
  echo "ℹ️  Using default Docker registry: $OH_RUNTIME_RUNTIME_IMAGE_REPO"
  echo "   (Set OH_RUNTIME_RUNTIME_IMAGE_REPO to override)"
else
  echo "ℹ️  Using Docker registry: $OH_RUNTIME_RUNTIME_IMAGE_REPO"
fi
export OH_RUNTIME_RUNTIME_IMAGE_REPO

# Check if user is logged in to registry
REGISTRY_HOST=$(echo $OH_RUNTIME_RUNTIME_IMAGE_REPO | cut -d'/' -f1)
echo ""
echo "🔐 Checking Docker login for $REGISTRY_HOST..."

if docker info 2>/dev/null | grep -q "Username"; then
  echo "✅ Docker login detected"
else
  echo "⚠️  Warning: You may not be logged in to $REGISTRY_HOST"
  echo "   Images will be built but may fail to push."
  echo ""
  echo "   To login, run:"
  echo "   docker login $REGISTRY_HOST"
  echo ""
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

# Build the command
COMMAND="poetry run python evaluation/benchmarks/swe_bench/prebuild_images.py \
  --dataset $DATASET \
  --split $SPLIT \
  --num-workers $NUM_WORKERS \
  --no-skip-existing"

if [ -n "$EVAL_LIMIT" ]; then
  COMMAND="$COMMAND --eval-limit $EVAL_LIMIT"
fi

# Add optional flags from environment variables
if [ "$NO_PUSH" = "true" ]; then
  COMMAND="$COMMAND --no-push"
  echo "ℹ️  NO_PUSH=true: Images will not be pushed to registry"
fi

if [ "$FORCE_REBUILD" = "true" ]; then
  COMMAND="$COMMAND --force-rebuild"
  echo "ℹ️  FORCE_REBUILD=true: All images will be rebuilt"
fi

if [ -n "$PLATFORM" ]; then
  COMMAND="$COMMAND --platform $PLATFORM"
  echo "ℹ️  Building for platform: $PLATFORM"
fi

# if [ "$NO_SKIP_EXISTING" = "true" ]; then
#   COMMAND="$COMMAND --no-skip-existing"
#   echo "ℹ️  NO_SKIP_EXISTING=true: Will rebuild existing images"
# fi

if [ "$ENABLE_BROWSER" = "true" ]; then
  COMMAND="$COMMAND --enable-browser"
  echo "⚠️  ENABLE_BROWSER=true: Building with browser support"
  echo "    Make sure to set RUN_WITH_BROWSING=true when running evaluations!"
fi

if [ "$NO_CLEANUP" = "true" ]; then
  COMMAND="$COMMAND --no-cleanup"
  echo "⚠️  NO_CLEANUP=true: Local images will NOT be removed after push"
  echo "    This may consume 150-200GB+ of disk space!"
else
  echo "ℹ️  Auto-cleanup enabled: Local images will be removed after push to save disk space"
fi

if [ -n "$MAX_PUSH_RETRIES" ]; then
  COMMAND="$COMMAND --max-push-retries $MAX_PUSH_RETRIES"
  echo "ℹ️  MAX_PUSH_RETRIES=$MAX_PUSH_RETRIES: Docker push will retry up to $MAX_PUSH_RETRIES times on failure"
fi

echo ""
echo "🚀 Starting image pre-build process..."
echo ""
echo "Command: $COMMAND"
echo ""

# Run the pre-build script
eval $COMMAND

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo ""
  echo "=========================================="
  echo "✅ Pre-build completed successfully!"
  echo "=========================================="
  echo ""
  echo "Next steps:"
  echo "1. Verify images in registry: $OH_RUNTIME_RUNTIME_IMAGE_REPO"
  echo "2. Run evaluation normally - it will pull pre-built images"
  echo ""
else
  echo ""
  echo "=========================================="
  echo "❌ Pre-build failed with exit code $EXIT_CODE"
  echo "=========================================="
  echo ""
  echo "Check the logs above for error details."
  echo ""
fi

exit $EXIT_CODE
