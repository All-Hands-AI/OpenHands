#!/bin/bash
set -e

# This entrypoint script runs as root to fix workspace ownership before switching to openhands user

echo "🔧 OpenHands Runtime Entrypoint - Fixing workspace ownership..."

# Check if /workspace exists and fix ownership
if [ -d "/workspace" ]; then
    echo "📁 Found /workspace directory, checking ownership..."
    ls -la /workspace
    
    # Fix ownership to openhands:openhands
    echo "🔧 Changing ownership to openhands:openhands..."
    chown -R openhands:openhands /workspace
    chmod -R g+rw /workspace
    
    echo "✅ Ownership fixed:"
    ls -la /workspace
else
    echo "⚠️  /workspace directory not found, will be created later"
fi

# If arguments are provided, execute them as the openhands user
if [ $# -gt 0 ]; then
    echo "🚀 Switching to openhands user and executing: $@"
    # Use exec to replace the current process and preserve all arguments
    exec su openhands -c "exec \"\$@\"" -- "$@"
else
    echo "🚀 Switching to openhands user with bash shell"
    exec su - openhands
fi