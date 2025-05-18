#!/bin/bash
set -eo pipefail

echo "Starting Tradejoy Backend..."

# Print versions for debugging
echo "Python version: $(python --version)"
echo "Poetry version: $(poetry --version)"

# Verify Docker CLI is working
echo "Docker version: $(docker --version || echo 'Docker not installed or not accessible')"

# Create workspace directory if it doesn't exist
mkdir -p "${WORKSPACE_BASE:-/tmp/workspace}"
chmod 777 "${WORKSPACE_BASE:-/tmp/workspace}"

# Fix Docker socket permissions if needed
if [ -e "/var/run/docker.sock" ]; then
  echo "Setting proper permissions for Docker socket"
  
  # Try to get Docker socket group ID
  DOCKER_SOCKET_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || echo "999")
  echo "Docker socket group id: $DOCKER_SOCKET_GID"
  
  # Create docker group with the right GID if it doesn't exist
  if ! getent group $DOCKER_SOCKET_GID >/dev/null; then
    echo "Creating docker group with GID $DOCKER_SOCKET_GID"
    groupadd -g $DOCKER_SOCKET_GID docker 2>/dev/null || true
  fi
  
  # Add current user to docker group
  usermod -aG $DOCKER_SOCKET_GID root 2>/dev/null || true
  
  # Try to make socket accessible
  chmod 666 /var/run/docker.sock 2>/dev/null || echo "Could not change socket permissions"
  
  # Test Docker connectivity
  echo "Testing Docker connection:"
  if docker info >/dev/null 2>&1; then
    echo "✅ Docker socket is accessible and working!"
  else
    echo "⚠️ WARNING: Docker socket permission issue detected."
    echo "Docker-in-Docker functionality might not work properly."
    
    # Set DOCKER_HOST as fallback
    export DOCKER_HOST=unix:///var/run/docker.sock
  fi
else
  echo "⚠️ WARNING: Docker socket not found at /var/run/docker.sock"
  echo "Docker-in-Docker functionality will not work."
fi

# Create AWS config directory if needed
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Configuring AWS credentials..."
  mkdir -p /root/.aws
  
  # Create credentials file
  cat > /root/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = ${AWS_REGION:-us-east-1}
EOF

  # Create config file
  cat > /root/.aws/config << EOF
[default]
region = ${AWS_REGION:-us-east-1}
output = json
EOF

  # Set permissions
  chmod 600 /root/.aws/credentials
  chmod 600 /root/.aws/config
  
  echo "AWS credentials configured successfully"
fi

# Ensure sandbox is properly configured
if [ -f "/app/config.toml" ]; then
  # Read existing config
  CONFIG_CONTENT=$(cat /app/config.toml)
  
  # Make sure sandbox section exists
  if ! echo "$CONFIG_CONTENT" | grep -q "\[sandbox\]"; then
    echo "Adding sandbox section to config.toml"
    cat >> /app/config.toml << EOF

[sandbox]
runtime_container_image = "${SANDBOX_RUNTIME_CONTAINER_IMAGE:-ghcr.io/all-hands-ai/runtime:0.38-nikolaik}"
use_host_network = false
runtime_binding_address = "0.0.0.0"
keep_runtime_alive = true
EOF
  fi

  # Make sure the workspace_base path is correct
  if grep -q "workspace_base.*\/app\/workspace" /app/config.toml; then
    echo "Updating workspace path in config.toml from /app/workspace to /tmp/workspace"
    sed -i 's|workspace_base.*"/app/workspace"|workspace_base = "/tmp/workspace"|g' /app/config.toml
  fi
fi

# Add env vars that might be used by AWS SDK
export AWS_SDK_LOAD_CONFIG=1

# Start the application
echo "Starting application..."
exec "$@" 