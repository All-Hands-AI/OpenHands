# Runtime Configuration Guide

OpenHands supports multiple runtime environments for executing agent actions. This guide explains the available options and how to configure them.

## Available Runtimes

### 1. Local Runtime (Recommended for Railway/Cloud Deployments)
- **Name**: `local`
- **Description**: Runs the action execution server directly on the local machine without Docker
- **Use Case**: Cloud deployments, Railway, environments where Docker is not available
- **Configuration**: Set `runtime = "local"` in config.toml or `RUNTIME=local` environment variable

### 2. Docker Runtime
- **Name**: `docker`
- **Description**: Runs actions in Docker containers
- **Use Case**: Local development with Docker available
- **Requirements**: Docker daemon must be running
- **Configuration**: Set `runtime = "docker"` in config.toml or `RUNTIME=docker` environment variable

### 3. Remote Runtime
- **Name**: `remote`
- **Description**: Connects to a remote runtime API service
- **Use Case**: Kubernetes clusters, distributed deployments
- **Requirements**: Remote runtime API service must be running and accessible
- **Configuration**: Set `runtime = "remote"` in config.toml or `RUNTIME=remote` environment variable

## Default Configuration

As of this version, the default runtime is set to `local` to ensure compatibility with cloud deployments like Railway where Docker may not be available.

## Automatic Fallback

If the `remote` runtime is configured but the remote runtime API is not available, the system will automatically fall back to the `local` runtime with a warning message.

## Environment Variables

You can override the runtime configuration using environment variables:

```bash
# Use local runtime (recommended for Railway)
export RUNTIME=local

# Use Docker runtime (requires Docker)
export RUNTIME=docker

# Use remote runtime (requires remote service)
export RUNTIME=remote
```

## Troubleshooting

### "Connection refused" errors
If you see connection refused errors, it usually means:
1. You're using `remote` runtime but the remote service is not running
2. The system will automatically fall back to `local` runtime

### Railway Deployment
For Railway deployments, use `local` runtime:
```bash
RUNTIME=local
```

### Local Development
For local development with Docker:
```bash
RUNTIME=docker
```