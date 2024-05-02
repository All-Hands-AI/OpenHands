#!/bin/bash
# This script sets up the Docker environment for the project by pulling the required image and checking essential tools within the container.

export SANDBOX_CONTAINER_IMAGE="node:21-bullseye"
echo "Pulling the latest Docker image: $SANDBOX_CONTAINER_IMAGE"
docker pull $SANDBOX_CONTAINER_IMAGE

echo "Checking node, npm, and sudo availability in the Docker image..."
echo "Node.js version:"
docker run --rm $SANDBOX_CONTAINER_IMAGE node --version

echo "npm version:"
docker run --rm $SANDBOX_CONTAINER_IMAGE npm --version

echo "sudo version:"
docker run --rm $SANDBOX_CONTAINER_IMAGE sudo --version
