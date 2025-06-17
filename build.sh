#!/usr/bin/env bash
set -e

# Build the package using python -m build (which works with hatchling)
python -m build -v
