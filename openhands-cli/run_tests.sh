#!/bin/bash
# Script to run tests with clean PYTHONPATH to avoid conflicts with openhands/code
# This ensures tests use the proper openhands.sdk imports from the virtual environment

cd "$(dirname "$0")"
PYTHONPATH="" uv run pytest tests/ "$@"