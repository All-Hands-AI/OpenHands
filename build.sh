#!/usr/bin/env bash
set -e

# Disable SSL/TLS verification for Poetry and its underlying libraries
export PYTHONHTTPSVERIFY=0
export REQUESTS_CA_BUNDLE=""
export CURL_CA_BUNDLE=""
export SSL_CERT_FILE=""
export POETRY_REQUESTS_TIMEOUT=60

poetry build -v
