# OpenHands Cloud Deployment Guide

This guide explains how to deploy OpenHands in a cloud environment with multi-user support and authentication.

## Architecture Overview

The cloud deployment of OpenHands consists of the following components:

1. **Frontend**: Nginx serving the React application
2. **Backend**: FastAPI application with user authentication
3. **Database**: PostgreSQL for user data and settings
4. **Cache**: Redis for session management and caching
5. **Kubernetes**: For container orchestration and scaling

## Deployment Options

### Option 1: Docker Compose (Development/Testing)

For development or small-scale deployments, you can use Docker Compose:

```bash
# Set required environment variables
export DB_USER=your_db_user
export DB_PASSWORD=your_secure_password
export DB_NAME=openhands
export JWT_SECRET=your_secure_jwt_secret

# Build and start all services
docker-compose -f docker-compose.cloud.yml up -d

# View logs
docker-compose -f docker-compose.cloud.yml logs -f

# Stop all services
docker-compose -f docker-compose.cloud.yml down
```

### Option 2: Kubernetes (Production)

For production deployments, use Kubernetes:

```bash
# Create a .env file with your configuration
cat > .env << EOL
export DB_USER=your_db_user
export DB_PASSWORD=your_secure_password
export DB_NAME=openhands
export JWT_SECRET=your_secure_jwt_secret

# Base64 encode secrets for Kubernetes
export DB_PASSWORD_BASE64=$(echo -n "$DB_PASSWORD" | base64)
export JWT_SECRET_BASE64=$(echo -n "$JWT_SECRET" | base64)
EOL

# Source the environment variables
source .env

# Process template files with environment variables
envsubst < kubernetes/postgres.yaml | kubectl apply -f -
envsubst < kubernetes/backend.yaml | kubectl apply -f -
kubectl apply -f kubernetes/redis.yaml
kubectl apply -f kubernetes/frontend.yaml
kubectl apply -f kubernetes/ingress.yaml

# Check deployment status
kubectl get pods

# View logs
kubectl logs -l app=openhands-backend
```

## Configuration

### Environment Variables

The following environment variables must be configured:

- `DB_HOST`: PostgreSQL host (default: postgres)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_USER`: PostgreSQL username
- `DB_PASSWORD`: PostgreSQL password
- `DB_NAME`: PostgreSQL database name
- `REDIS_HOST`: Redis host (default: redis)
- `REDIS_PORT`: Redis port (default: 6379)
- `JWT_SECRET`: Secret key for JWT tokens

### Security Considerations

For production deployments:

1. **Never hardcode secrets** in configuration files or source code
2. Use Kubernetes Secrets or a secure vault solution (HashiCorp Vault, AWS Secrets Manager, etc.)
3. Set a strong JWT_SECRET with high entropy
4. Enable HTTPS with proper certificates
5. Configure proper network policies in Kubernetes
6. Set up regular database backups
7. Implement proper access controls and RBAC
8. Regularly rotate credentials and secrets

## Scaling

The Kubernetes deployment supports horizontal scaling:

```bash
# Scale backend to 5 replicas
kubectl scale deployment openhands-backend --replicas=5

# Scale frontend to 3 replicas
kubectl scale deployment openhands-frontend --replicas=3
```

## Monitoring

For monitoring, you can deploy Prometheus and Grafana:

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Install Prometheus and Grafana
helm install monitoring prometheus-community/kube-prometheus-stack
```

## Troubleshooting

Common issues and solutions:

1. **Database connection errors**: Check DB credentials and network connectivity
2. **Authentication issues**: Verify JWT_SECRET is consistent across all backend instances
3. **Scaling problems**: Ensure PVCs are configured correctly for stateful components

For more help, check the logs or contact support.
