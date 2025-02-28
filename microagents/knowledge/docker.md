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
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

## Starting Docker in Container Environments

If you're in a container environment without systemd (like this workspace), start Docker with:

```bash
# Start Docker daemon in the background
sudo dockerd > /tmp/docker.log 2>&1 &

# Wait for Docker to initialize
sleep 5
```

## Basic Docker Commands

```bash
# Pull an image
docker pull nginx:latest

# Run a container
docker run -d -p 8080:80 --name my-nginx nginx:latest

# List running containers
docker ps

# Stop a container
docker stop my-nginx

# Remove a container
docker rm my-nginx

# List images
docker images

# Remove an image
docker rmi nginx:latest

# Build an image from a Dockerfile
docker build -t my-app:latest .
```

## Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: example
```

Run with:

```bash
docker-compose up -d
```

Stop with:

```bash
docker-compose down
```

## Docker Networking

```bash
# Create a network
docker network create my-network

# Run containers on the network
docker run -d --network my-network --name db postgres:latest
docker run -d --network my-network --name web nginx:latest

# Inspect network
docker network inspect my-network
```

## Docker Volumes

```bash
# Create a volume
docker volume create my-volume

# Run a container with a volume
docker run -d -v my-volume:/data --name my-container nginx:latest

# Inspect volume
docker volume inspect my-volume
```

## Best Practices

1. Use official images when possible
2. Keep images small by using multi-stage builds
3. Use .dockerignore to exclude unnecessary files
4. Don't run containers as root
5. Use environment variables for configuration
6. Tag images with specific versions
7. Use health checks to monitor container status