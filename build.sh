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

echo "Installing build tools..."
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org build wheel setuptools

echo "Building package using python -m build (no isolation to avoid SSL issues)..."
# Create/clean dist directory
mkdir -p dist
rm -rf dist/*

# Use python -m build with --no-isolation to respect our SSL configuration
# This is the PEP 517 standard way to build Python packages
python -m build --no-isolation

echo "Build completed successfully!"
ls -lh dist/
