#!/usr/bin/env bash
set -e

# Disable SSL/TLS verification for Poetry and its underlying libraries
export PYTHONHTTPSVERIFY=0
export REQUESTS_CA_BUNDLE=""
export CURL_CA_BUNDLE=""
export SSL_CERT_FILE=""
export POETRY_REQUESTS_TIMEOUT=60

# Set up pip configuration to disable SSL verification
export PIP_CONFIG_FILE="$(pwd)/pip.conf"
mkdir -p ~/.config/pip
cp pip.conf ~/.config/pip/pip.conf 2>/dev/null || true
mkdir -p ~/.pip
cp pip.conf ~/.pip/pip.conf 2>/dev/null || true

# Pre-install poetry-core to avoid SSL issues during build
echo "Pre-installing poetry-core..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org poetry-core 2>/dev/null || true

echo "Building package..."
poetry build -v
