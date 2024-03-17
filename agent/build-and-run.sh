#!/bin/bash
set -eo pipefail

rm -rf `pwd`/workspace
mkdir -p `pwd`/workspace

docker build -t control-loop .
docker run -e DEBUG=$DEBUG -e OPENAI_API_KEY=$OPENAI_API_KEY -v `pwd`/workspace:/workspace control-loop python /app/main.py /workspace "${1}"

