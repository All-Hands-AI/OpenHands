# OpenHands Development Workflows

## Review & Debugging Process

### Prerequisites
- Docker installed
- Python 3.12+
- `poetry` package manager

### Debugging MCP Server
```bash
# Run with verbose logging
docker run -it --rm \
  -e MCP_ENABLED=true \
  -e MCP_LOGGING=debug \
  -p 8000:8000 \
  -v $(pwd):/app \
  docker.all-hands.dev/all-hands-ai/openhands:0.30

# View logs
docker logs -f [CONTAINER_ID]
```

### Testing Endpoints
```bash
# Test MCP endpoints
curl -v http://localhost:8000/mcp/openhands://config
curl -N http://localhost:8000/mcp
```

## Deployment Workflow

### CI/CD Pipeline
1. **On PR Merge**:
   - Runs unit/integration tests
   - Builds Docker image
   - Pushes to registry with `:latest` tag

2. **Production Deployment**:
```bash
# Kubernetes example
kubectl apply -f k8s/deployment.yaml

# Docker Swarm
docker stack deploy -c docker-compose.prod.yml openhands
```

### Manual Deployment
```bash
# Pull latest image
docker pull docker.all-hands.dev/all-hands-ai/openhands:latest

# Run production instance
docker run -d --name openhands-prod \
  -p 3000:3000 \
  -p 8000:8000 \
  -v openhands-data:/.openhands-state \
  docker.all-hands.dev/all-hands-ai/openhands:latest
```

### Rollback Procedure
```bash
# Revert to previous version
docker run -d --name openhands-rollback \
  -p 3000:3000 \
  docker.all-hands.dev/all-hands-ai/openhands:0.29
```

## Monitoring
```bash
# View running services
docker ps

# Check logs
docker logs openhands-prod

# Health check
curl -I http://localhost:3000/health
```