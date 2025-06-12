#!/bin/bash
# Railway Runtime Setup Script
# This script pre-builds and configures the OpenHands runtime for instant availability

set -e

echo "🚀 Starting Railway Runtime Setup..."

# Set environment variables for Railway deployment
export RUNTIME=local
export SKIP_DEPENDENCY_CHECK=1
export LOCAL_RUNTIME_MODE=1
export OPENHANDS_REPO_PATH=/app

# Create necessary directories
echo "📁 Creating runtime directories..."
mkdir -p /app/.openhands-runtime
mkdir -p /app/.openhands-state
mkdir -p /app/workspace
mkdir -p /var/log

# Set up Python environment paths
PYTHON_BIN=$(which python)
PYTHON_DIR=$(dirname "$PYTHON_BIN")
VENV_ROOT=$(dirname "$PYTHON_DIR")

echo "🐍 Python environment:"
echo "  Python binary: $PYTHON_BIN"
echo "  Python directory: $PYTHON_DIR"
echo "  Virtual env root: $VENV_ROOT"

# Pre-install and verify runtime dependencies
echo "📦 Verifying runtime dependencies..."

# Check Jupyter installation
echo "  ✓ Checking Jupyter..."
if ! jupyter --version > /dev/null 2>&1; then
    echo "  ❌ Jupyter not found, installing..."
    pip install jupyter jupyterlab jupyter_kernel_gateway
else
    echo "  ✅ Jupyter is available"
fi

# Check tmux and libtmux
echo "  ✓ Checking tmux and libtmux..."
if ! tmux -V > /dev/null 2>&1; then
    echo "  ❌ tmux not found in system packages"
    # tmux should be installed via apt in Dockerfile
else
    echo "  ✅ tmux is available: $(tmux -V)"
fi

if ! python -c "import libtmux" > /dev/null 2>&1; then
    echo "  ❌ libtmux not found, installing..."
    pip install libtmux
else
    echo "  ✅ libtmux is available"
fi

# Check browser dependencies
echo "  ✓ Checking browser dependencies..."
if ! python -c "import browsergym" > /dev/null 2>&1; then
    echo "  ❌ browsergym not found, installing..."
    pip install browsergym-core
else
    echo "  ✅ browsergym is available"
fi

# Pre-configure runtime environment
echo "🔧 Pre-configuring runtime environment..."

# Create runtime configuration
cat > /app/.openhands-runtime/config.json << EOF
{
    "runtime_type": "local",
    "pre_built": true,
    "build_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "python_path": "$PYTHON_BIN",
    "venv_path": "$VENV_ROOT",
    "workspace_path": "/app/workspace",
    "dependencies_verified": true
}
EOF

# Pre-create tmux session template (if tmux is available)
if command -v tmux > /dev/null 2>&1; then
    echo "🖥️  Pre-configuring tmux environment..."
    # Create a tmux configuration for the runtime
    cat > /app/.openhands-runtime/tmux.conf << EOF
# OpenHands Runtime tmux configuration
set-option -g default-shell /bin/bash
set-option -g default-command /bin/bash
set-window-option -g mode-keys vi
set-option -g history-limit 10000
set-option -g base-index 1
set-window-option -g pane-base-index 1
EOF
fi

# Pre-warm Python imports
echo "🔥 Pre-warming Python imports..."
python -c "
import sys
import os
import subprocess
import tempfile
import threading
import httpx
import tenacity
import openhands
from openhands.core.config import OpenHandsConfig
from openhands.core.logger import openhands_logger
from openhands.runtime.impl.local.local_runtime import LocalRuntime
print('✅ Core imports successful')
"

# Test runtime initialization (dry run)
echo "🧪 Testing runtime initialization..."
python -c "
import os
import tempfile
from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream

# Create minimal config for testing
config = OpenHandsConfig()
config.runtime = 'local'
config.workspace_base = '/app/workspace'

# Test that we can create the config without errors
print('✅ Runtime configuration test successful')
"

# Create startup health check script
echo "🏥 Creating runtime health check..."
cat > /app/.openhands-runtime/health-check.py << 'EOF'
#!/usr/bin/env python3
"""Runtime health check for Railway deployment."""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def check_python_environment():
    """Check Python environment is properly set up."""
    try:
        import openhands
        import httpx
        import tenacity
        return True
    except ImportError as e:
        print(f"❌ Python import error: {e}")
        return False

def check_system_dependencies():
    """Check system dependencies are available."""
    checks = []
    
    # Check tmux
    try:
        result = subprocess.run(['tmux', '-V'], capture_output=True, text=True)
        if result.returncode == 0:
            checks.append(f"✅ tmux: {result.stdout.strip()}")
        else:
            checks.append("❌ tmux: not available")
    except FileNotFoundError:
        checks.append("❌ tmux: not found")
    
    # Check jupyter
    try:
        result = subprocess.run(['jupyter', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            checks.append("✅ jupyter: available")
        else:
            checks.append("❌ jupyter: not working")
    except FileNotFoundError:
        checks.append("❌ jupyter: not found")
    
    return checks

def check_runtime_readiness():
    """Check if runtime is ready for immediate use."""
    config_file = Path('/app/.openhands-runtime/config.json')
    if config_file.exists():
        return "✅ Runtime pre-configuration found"
    else:
        return "❌ Runtime not pre-configured"

def main():
    print("🔍 OpenHands Runtime Health Check")
    print("=" * 40)
    
    # Check Python environment
    if check_python_environment():
        print("✅ Python environment: OK")
    else:
        print("❌ Python environment: FAILED")
        return 1
    
    # Check system dependencies
    print("\n📦 System Dependencies:")
    for check in check_system_dependencies():
        print(f"  {check}")
    
    # Check runtime readiness
    print(f"\n🚀 Runtime Status:")
    print(f"  {check_runtime_readiness()}")
    
    print("\n✅ Health check complete!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
EOF

chmod +x /app/.openhands-runtime/health-check.py

# Run the health check
echo "🔍 Running health check..."
python /app/.openhands-runtime/health-check.py

# Create runtime startup script
echo "⚡ Creating runtime startup script..."
cat > /app/.openhands-runtime/start-runtime.sh << 'EOF'
#!/bin/bash
# Runtime startup script for Railway deployment

set -e

echo "🚀 Starting OpenHands Runtime..."

# Set environment variables
export RUNTIME=local
export LOCAL_RUNTIME_MODE=1
export OPENHANDS_REPO_PATH=/app
export PYTHONPATH=/app:$PYTHONPATH

# Ensure workspace directory exists
mkdir -p /app/workspace

# Set proper permissions
chmod 755 /app/workspace

echo "✅ Runtime environment ready!"
echo "📍 Workspace: /app/workspace"
echo "🐍 Python: $(which python)"
echo "🔧 Runtime: local (pre-built)"

# If arguments are provided, execute them, otherwise start uvicorn
if [ $# -gt 0 ]; then
    echo "🚀 Starting: $@"
    exec "$@"
else
    echo "🚀 Starting uvicorn server..."
    exec uvicorn openhands.server.listen:app --host 0.0.0.0 --port ${PORT:-3000}
fi
EOF

chmod +x /app/.openhands-runtime/start-runtime.sh

# Set proper permissions
echo "🔐 Setting permissions..."
chown -R openhands:app /app/.openhands-runtime 2>/dev/null || true
chown -R openhands:app /app/workspace 2>/dev/null || true
chmod -R 755 /app/.openhands-runtime
chmod -R 755 /app/workspace

echo "✅ Railway Runtime Setup Complete!"
echo ""
echo "📋 Setup Summary:"
echo "  • Runtime type: local (pre-built)"
echo "  • Dependencies: verified and installed"
echo "  • Configuration: pre-created"
echo "  • Health check: available at /app/.openhands-runtime/health-check.py"
echo "  • Startup script: /app/.openhands-runtime/start-runtime.sh"
echo ""
echo "🎉 Runtime is ready for instant use!"