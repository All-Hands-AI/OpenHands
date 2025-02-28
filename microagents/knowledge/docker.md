---
name: docker
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- docker
- container
---

# Docker Installation and Usage Guide

## Installation on Debian/Ubuntu Systems

To install Docker on a Debian/Ubuntu system, follow these steps:

```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
sudo apt-get update

# Install Docker Engine
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

## Starting Docker in Container Environments

If you're in a container environment without systemd (like this workspace), start Docker with:

```bash
# Start Docker daemon in the background
sudo dockerd > /tmp/docker.log 2>&1 &

# Wait for Docker to initialize
sleep 5
```

## Verifying Docker Installation

To verify Docker is working correctly, run the hello-world container:

```bash
sudo docker run hello-world
```

## Common Docker Commands

```bash
# List running containers
docker ps

# List all containers (including stopped ones)
docker ps -a

# Pull an image
docker pull [IMAGE_NAME]

# Run a container
docker run [OPTIONS] [IMAGE_NAME] [COMMAND]

# Build an image from a Dockerfile
docker build -t [NAME:TAG] [PATH_TO_DOCKERFILE_DIR]

# Stop a container
docker stop [CONTAINER_ID/NAME]

# Remove a container
docker rm [CONTAINER_ID/NAME]

# Remove an image
docker rmi [IMAGE_ID/NAME]

# View logs
docker logs [CONTAINER_ID/NAME]

# Execute a command in a running container
docker exec -it [CONTAINER_ID/NAME] [COMMAND]
```

## Docker Compose

If you need to manage multi-container applications, Docker Compose is already installed with the Docker installation above.

```bash
# Start services defined in docker-compose.yml
docker-compose up -d

# Stop services
docker-compose down
```