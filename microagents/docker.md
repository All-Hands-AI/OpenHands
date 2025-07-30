---
name: docker
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- docker
- container
---

# Docker Usage Guide

## Starting Docker in Container Environments

To start Docker in a container environment:

```bash
# Configure Docker daemon with MTU 1450 to prevent packet fragmentation issues
sudo mkdir -p /etc/docker
echo '{"mtu": 1450}' | sudo tee /etc/docker/daemon.json > /dev/null

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
