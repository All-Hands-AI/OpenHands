#!/usr/bin/env bash
set -e

# Disable SSL/TLS verification for Poetry
export POETRY_REQUESTS_TIMEOUT=60
poetry config certificates.default.cert false 2>/dev/null || true
poetry config certificates.default.verify false 2>/dev/null || true

poetry build -v
