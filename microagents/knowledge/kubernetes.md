---
name: kubernetes
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- kubernetes
- k8s
- kind
---

# Kubernetes Local Development with KIND

## KIND Installation and Setup

KIND (Kubernetes IN Docker) is a tool for running local Kubernetes clusters using Docker containers as nodes. It's designed for testing Kubernetes applications locally.

### Installation

To install KIND on a Debian/Ubuntu system:

```bash
# Download KIND binary
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
# Make it executable
chmod +x ./kind
# Move to a directory in your PATH
sudo mv ./kind /usr/local/bin/
```

To install kubectl:

```bash
# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
# Make it executable
chmod +x kubectl
# Move to a directory in your PATH
sudo mv ./kubectl /usr/local/bin/
```

### Creating a Cluster

Create a basic KIND cluster:

```bash
kind create cluster
```

For a more customized setup, create a configuration file:

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
```