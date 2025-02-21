#!/usr/bin/env bash

# Step 1: Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -q)

# Step 2: Remove all containers (running and stopped)
echo "Removing all containers..."
docker rm $(docker ps -a -q)

# Optional: Remove all Docker images (if you want to clean up images too)
# echo "Removing all Docker images..."
# docker rmi $(docker images -q)

echo "All containers have been removed."
