# Tradejoy Backend Container

This container provides a headless backend for Tradejoy based on OpenHands without the frontend UI components.

## Features

- Headless backend that serves the API only (no UI)
- Docker-in-Docker functionality for chat runtime
- Proper sandbox configuration for OpenHands
- AWS integration for Bedrock LLM

## Building and Running

### Build the Image

```bash
docker-compose -f tradejoy/containers/docker-compose.yml build
```

### Run the Container

```bash
docker-compose -f tradejoy/containers/docker-compose.yml up
```

## Environment Variables

The container accepts the following environment variables:

- `SANDBOX_RUNTIME_CONTAINER_IMAGE`: Docker image for the runtime (default: ghcr.io/all-hands-ai/runtime:0.38-nikolaik)
- `WORKSPACE_BASE`: Path to the workspace directory (default: ./workspace)
- `AWS_ACCESS_KEY_ID`: AWS access key (for Bedrock)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (for Bedrock)
- `AWS_REGION`: AWS region (default: us-east-1)

## API Endpoints

The backend server exposes REST API endpoints on port 3000. You can interact with it using:

- REST API: http://localhost:3000/api/
- WebSocket: ws://localhost:3000/socket.io/

## Troubleshooting

### Docker Socket Issues

If you encounter Docker connectivity problems:

1. Make sure your host's Docker daemon is running
2. Check that the Docker socket is properly mounted in the container
3. Verify that the socket permissions allow the container to access it

### Workspace Issues

If files aren't persisting:

1. Make sure the workspace directory is properly mounted
2. Check that the WORKSPACE_BASE environment variable is set correctly

### AWS Connectivity

For AWS/Bedrock issues:

1. Verify your AWS credentials are correct
2. Ensure the Bedrock service is available in your AWS region
3. Check that your account has access to the Bedrock model specified in config.toml 