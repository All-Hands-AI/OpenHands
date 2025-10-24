#!/bin/bash
# Enterprise pytest command
# The PYTHONPATH environment variable is not needed because it's configured in pyproject.toml

uv run --project=enterprise pytest \
  --forked \
  -n auto \
  -s \
  -p no:ddtrace \
  -p no:ddtrace.pytest_bdd \
  -p no:ddtrace.pytest_benchmark \
  ./enterprise/tests/unit \
  --cov=enterprise \
  --cov-branch
