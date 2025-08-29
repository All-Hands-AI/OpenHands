#!/usr/bin/env bash

# WebArena environment configuration
# This script sets up the environment variables needed for WebArena evaluation

# Check if WEBARENA_BASE_URL is set
if [ -z "$WEBARENA_BASE_URL" ]; then
    echo "Warning: WEBARENA_BASE_URL is not set. Please set it to the base URL where webarena services are hosted."
    echo "Example: export WEBARENA_BASE_URL=http://your-webarena-host"
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY is not set. Please set it to your OpenAI API key."
fi

echo "WebArena environment configured:"
echo "  WEBARENA_BASE_URL: $WEBARENA_BASE_URL"
echo "  OPENAI_API_KEY: ${OPENAI_API_KEY:+[SET]}${OPENAI_API_KEY:-[NOT SET]}"
