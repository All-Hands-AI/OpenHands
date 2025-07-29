#! /bin/bash

echo "Setting up the environment..."

# Only set INSTALL_DOCKER=0 if docker command is not available
if ! command -v docker >/dev/null 2>&1; then
    echo "Docker command not found, setting INSTALL_DOCKER=0"
    export INSTALL_DOCKER=0
fi

make build

#run a minimal pre-commit script to trigger its setup. Otherwhise it will cause
#the first commit to time-out.
poetry run pre-commit run --files ./README.md --config ./dev_config/python/.pre-commit-config.yaml


