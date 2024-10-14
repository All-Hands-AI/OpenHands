#!/bin/bash
# Build and run OpenHands with OpenHands.

set -euo pipefail

function get_docker() {
    echo "Docker is required to build and run OpenHands."
    echo "https://docs.docker.com/get-started/get-docker/"
    exit 1
}

function check_tools() {
	command -v docker &>/dev/null || get_docker
}

function exit_if_indocker() {
    if [ -f /.dockerenv ]; then
        echo "Running inside a Docker container. Exiting..."
        exit 1
    fi
}

#
exit_if_indocker

check_tools

##
OPENHANDS_WORKSPACE=$(git rev-parse --show-toplevel)

##
# app
export DATE="dev"

export SANDBOX_BASE_CONTAINER_IMAGE="openhands-dev"
SANDBOX_USER_ID=$(id -u) && export SANDBOX_USER_ID

export PORT="${PORT:-3000}"

export WORKSPACE_BASE="${OPENHANDS_WORKSPACE}"
export CONFIG_FILE="${OPENHANDS_WORKSPACE}/containers/dev/dev-config.toml"
#
export OPENHANDS_WORKSPACE

##
cd "$OPENHANDS_WORKSPACE/" || exit 1

# custom sandbox for openhands
docker compose -f containers/dev/compose.yml build dev

# openhands dev ui/backend running in a container
# this repo will be mounted as workspace
docker buildx bake openhands
docker compose up -d "$@" openhands
##
