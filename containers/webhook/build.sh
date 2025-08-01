#!/bin/bash

# Build the OpenHands webhook container

set -e

# Navigate to the root directory
cd "$(dirname "$0")/../.."

# Build the Docker image
echo "Building OpenHands webhook container..."
docker build -t openhands-webhook -f containers/webhook/Dockerfile .

echo "Build complete! You can now run the container with:"
echo "docker run -p 8000:8000 -e GITHUB_WEBHOOK_SECRET=your_secret_here openhands-webhook"
echo ""
echo "Or use docker-compose:"
echo "cd containers/webhook && docker-compose up -d"