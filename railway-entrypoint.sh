#!/bin/bash
set -e

# Railway entrypoint script for OpenHands with Docker-in-Docker support

echo "Starting OpenHands Railway deployment with supervisor..."

# Function to cleanup on exit
cleanup() {
    echo "Shutting down..."
    supervisorctl stop all 2>/dev/null || true
    killall supervisord 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Ensure we're running as root
if [ "$(id -u)" != "0" ]; then
    echo "This script must run as root for Docker daemon access"
    exit 1
fi

# Create necessary directories with proper permissions
echo "Setting up directories and permissions..."
mkdir -p $FILE_STORE_PATH $WORKSPACE_BASE /var/lib/docker /var/log
chown -R openhands:app $FILE_STORE_PATH $WORKSPACE_BASE
chmod -R 770 $FILE_STORE_PATH $WORKSPACE_BASE

# Ensure Docker socket directory exists
mkdir -p /var/run
chmod 755 /var/run

# Pre-pull the runtime container image in background after Docker starts
echo "Setting up runtime image pull..."
cat > /usr/local/bin/pull-runtime-image.sh << 'EOF'
#!/bin/bash
# Wait for Docker to be ready
for i in {1..60}; do
    if docker version >/dev/null 2>&1; then
        echo "Docker is ready, pulling runtime image..."
        docker pull $SANDBOX_RUNTIME_CONTAINER_IMAGE &
        echo "Runtime image pull started in background"
        exit 0
    fi
    echo "Waiting for Docker to be ready... ($i/60)"
    sleep 1
done
echo "Docker failed to start within timeout"
exit 1
EOF
chmod +x /usr/local/bin/pull-runtime-image.sh

# Start the background image pull
/usr/local/bin/pull-runtime-image.sh &

echo "Starting supervisor to manage Docker and OpenHands..."
# Start supervisor with our configuration
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
