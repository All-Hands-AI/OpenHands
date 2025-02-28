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

Then create the cluster with:

```bash
kind create cluster --config kind-config.yaml
```

### Working with the Cluster

After creating a cluster, kubectl is automatically configured to use it:

```bash
# Verify the cluster is running
kubectl cluster-info

# Create a namespace
kubectl create namespace my-namespace

# Apply Kubernetes manifests
kubectl apply -f my-deployment.yaml

# View resources
kubectl get pods -n my-namespace
```

### Loading Docker Images

When working with local images, load them directly into KIND:

```bash
# Build your Docker image
docker build -t my-app:latest .

# Load the image into KIND
kind load docker-image my-app:latest
```

### Creating Kubernetes Secrets

Create secrets for Docker registry authentication:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry-server> \
  --docker-username=<your-username> \
  --docker-password=<your-password> \
  --docker-email=<your-email>
```

Create generic secrets:

```bash
kubectl create secret generic my-secret \
  --from-literal=key1=value1 \
  --from-literal=key2=value2
```

### Deleting the Cluster

When you're done, delete the cluster:

```bash
kind delete cluster
```

## Best Practices

1. Use namespaces to organize resources
2. Set resource limits for deployments
3. Use ConfigMaps and Secrets for configuration
4. Implement health checks with liveness and readiness probes
5. Use port-forwarding for local access to services