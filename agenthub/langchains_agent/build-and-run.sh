#!/bin/bash
set -eo pipefail

rm -rf `pwd`/workspace
mkdir -p `pwd`/workspace

pushd agenthub/langchains_agent
docker build -t control-loop .
popd
docker run \
    -e DEBUG=$DEBUG \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    -u `id -u`:`id -g` \
    -v `pwd`/workspace:/workspace \
    -v `pwd`:/app:ro \
    -e PYTHONPATH=/app \
    control-loop \
    python /app/opendevin/main.py -d /workspace -t "${1}" 

