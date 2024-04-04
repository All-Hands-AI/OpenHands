#!/usr/bin/env bash

[[ ! -z "${DEBUG}" ]]; set -eux

update-ca-certificates

#curl http://ollama:11434/api/tags
# curl -X POST http://ollama:11434/api/pull -d '{"name": "'${OLLAMA_MODEL}'"}'
# curl http://ollama:11434/api/generate -d '{"model": "'${OLLAMA_MODEL}'"}'

source ${VENV_DIR}/bin/activate

[[ ! -z "${DEBUG}" ]]; litellm --help
litellm --file /etc/litellm_config.yaml --port "${LITELLM_PORT}"

memgpt run -y --agent devin_memory \
    --model "llama2" \
    --model-endpoint-type ollama \
    --model-endpoint http://ollama:11434 \
    --debug
