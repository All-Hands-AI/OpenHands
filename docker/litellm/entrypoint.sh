#!/bin/bash

if [ -n "${DEBUG}" ]; then set -eux; else set -eu; fi

if [ -n "${DEBUG}" ]; then litellm --help; fi
litellm --file /etc/litellm/config.yaml --port "${LITELLM_PORT}"
