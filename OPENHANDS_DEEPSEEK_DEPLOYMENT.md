# OpenHands with DeepSeek R1-0528 - Complete Local Deployment Guide

## 🚀 Complete Local Deployment of OpenHands with DeepSeek R1-0528 Integration

This guide provides step-by-step instructions to deploy and run the complete OpenHands application locally with our integrated DeepSeek R1-0528 model, ensuring full functionality of the AI software engineering agent.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Service Deployment](#service-deployment)
5. [Verification & Testing](#verification--testing)
6. [Development Workflow](#development-workflow)
7. [Troubleshooting](#troubleshooting)
8. [Production Considerations](#production-considerations)

## 🔧 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 20GB free space
- **CPU**: 4+ cores recommended
- **GPU**: Optional (NVIDIA GPU with 8GB+ VRAM for local model inference)

### Required Software
```bash
# Core dependencies
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- Make

# Optional for GPU acceleration
- NVIDIA Docker runtime (for GPU support)
- CUDA 11.8+ (for local model inference)
```

## 🛠️ Environment Setup

### 1. Clone and Setup Repository
```bash
# Navigate to your OpenHands directory (already cloned)
cd /workspace/CodeAgent03

# Verify our DeepSeek integration files
ls -la openhands/llm/deepseek_r1.py
ls -la openhands/llm/enhanced_llm.py
ls -la openhands/llm/fallback_manager.py
```

### 2. Install System Dependencies
```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    make \
    python3-dev \
    python3-pip \
    nodejs \
    npm \
    docker.io \
    docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 3. Install Python Dependencies
```bash
# Install Poetry (Python dependency manager)
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Install Python dependencies
make install

# Alternative: Direct pip installation
pip install -r requirements_deepseek.txt
```

### 4. Install Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to root directory
cd ..
```

## ⚙️ Configuration

### 1. Environment Variables Setup
```bash
# Create environment configuration file
cat > .env << 'EOF'
# =============================================================================
# OpenHands with DeepSeek R1-0528 Configuration
# =============================================================================

# LLM Configuration
LLM_MODEL=deepseek-r1-0528
LLM_API_KEY=your-deepseek-api-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_PROVIDER=deepseek

# Fallback Configuration
ENABLE_FALLBACK=true
FALLBACK_MODELS=deepseek-r1-0528,gpt-3.5-turbo
AUTO_FALLBACK_ON_ERROR=true

# OpenHands Configuration
SANDBOX_TYPE=local
WORKSPACE_BASE=/tmp/openhands_workspace
MAX_ITERATIONS=100
MAX_BUDGET_PER_TASK=10.0

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=3000
FRONTEND_PORT=3001

# Security Configuration
JWT_SECRET=your-jwt-secret-here
ALLOWED_ORIGINS=http://localhost:3001,http://127.0.0.1:3001

# Database Configuration (if using persistent storage)
DATABASE_URL=sqlite:///./openhands.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/tmp/openhands.log

# Development Configuration
DEBUG=true
HOT_RELOAD=true

# Docker Configuration
DOCKER_ENABLED=true
CONTAINER_IMAGE=openhands:latest

# Performance Configuration
MAX_CONCURRENT_SESSIONS=5
REQUEST_TIMEOUT=300
RESPONSE_CACHE_TTL=3600

# DeepSeek Specific Configuration
DEEPSEEK_MODEL_PATH=deepseek-ai/DeepSeek-R1-0528
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TOP_P=0.9

# Cost Management
ENABLE_COST_TRACKING=true
MAX_COST_PER_SESSION=5.0
COST_ALERT_THRESHOLD=3.0
EOF

# Load environment variables
source .env
export $(cat .env | grep -v '^#' | xargs)
```

### 2. Create Configuration File
```bash
# Create OpenHands configuration
cat > config.toml << 'EOF'
[core]
workspace_base = "/tmp/openhands_workspace"
persist_sandbox = false
run_as_openhands = true
runtime = "eventstream"
max_iterations = 100
max_budget_per_task = 10.0
enable_auto_lint = true

[llm]
model = "deepseek-r1-0528"
api_key = "your-deepseek-api-key-here"
base_url = "https://api.deepseek.com"
api_version = ""
embedding_model = ""
embedding_base_url = ""
embedding_api_key = ""
num_retries = 8
retry_wait_time = 120
retry_multiplier = 2
timeout = 600
temperature = 0.7
top_p = 0.9
max_tokens = 4096

# DeepSeek Fallback Configuration
enable_fallback = true
fallback_models = ["deepseek-r1-0528", "gpt-3.5-turbo"]
auto_fallback_on_error = true
fallback_retry_attempts = 3
fallback_cooldown_period = 300

[llm.fallback_api_keys]
"deepseek-r1-0528" = "your-deepseek-api-key-here"
"gpt-3.5-turbo" = "your-openai-api-key-here"

[agent]
name = "CodeActAgent"
memory_enabled = true
memory_max_threads = 3

[sandbox]
runtime_container_image = "openhands:latest"
user_id = 1000
use_host_network = false
timeout = 120
api_key = ""
remote_runtime_api_url = ""
keep_runtime_alive = false
runtime_startup_timeout = 600
runtime_startup_env_vars = {}

[security]
security_analyzer = ""
confirmation_mode = false
disable_auto_run = false

[ui]
default_agent = "CodeActAgent"
default_language = "en"
enable_analytics = false
EOF
```

### 3. Setup Workspace Directory
```bash
# Create workspace directory
sudo mkdir -p /tmp/openhands_workspace
sudo chown -R $USER:$USER /tmp/openhands_workspace
chmod 755 /tmp/openhands_workspace

# Create logs directory
mkdir -p logs
```

## 🚀 Service Deployment

### 1. Build Application
```bash
# Install pre-commit hooks
make install-pre-commit-hooks

# Build the complete application
make build

# Alternative: Build components separately
# make install  # Backend dependencies
# cd frontend && npm run build && cd ..  # Frontend build
```

### 2. Start Backend Services
```bash
# Method 1: Using Make (Recommended)
make start-backend

# Method 2: Direct Python execution
python -m openhands.server.listen \
    --host 0.0.0.0 \
    --port 3000 \
    --file-store-path /tmp/openhands_workspace \
    --config-file config.toml

# Method 3: Using uvicorn directly
uvicorn openhands.server.listen:app \
    --host 0.0.0.0 \
    --port 3000 \
    --reload \
    --log-level info
```

### 3. Start Frontend Services
```bash
# Open new terminal and navigate to frontend
cd frontend

# Start development server
npm run start

# Alternative: Production build and serve
npm run build
npm run serve
```

### 4. Docker Deployment (Alternative)
```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 5. Complete Startup Script
```bash
#!/bin/bash
# startup.sh - Complete OpenHands with DeepSeek startup script

set -e

echo "🚀 Starting OpenHands with DeepSeek R1-0528 Integration"
echo "======================================================="

# Load environment variables
if [ -f .env ]; then
    source .env
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm required but not installed."; exit 1; }
echo "✅ All dependencies found"

# Create workspace
echo "📁 Setting up workspace..."
mkdir -p /tmp/openhands_workspace
mkdir -p logs
echo "✅ Workspace created"

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v poetry >/dev/null 2>&1; then
    poetry install
else
    pip install -r requirements_deepseek.txt
fi
echo "✅ Python dependencies installed"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Build application
echo "🔨 Building application..."
make build
echo "✅ Application built"

# Start backend in background
echo "🖥️ Starting backend server..."
python -m openhands.server.listen \
    --host 0.0.0.0 \
    --port 3000 \
    --file-store-path /tmp/openhands_workspace \
    --config-file config.toml > logs/backend.log 2>&1 &

BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 10

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check logs/backend.log"
    exit 1
fi

# Test backend health
if curl -f http://localhost:3000/api/options >/dev/null 2>&1; then
    echo "✅ Backend health check passed"
else
    echo "⚠️ Backend health check failed, but continuing..."
fi

# Start frontend
echo "🌐 Starting frontend server..."
cd frontend
npm run start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 15

# Final status
echo ""
echo "🎉 OpenHands with DeepSeek R1-0528 is now running!"
echo "=================================================="
echo "🌐 Frontend: http://localhost:3001"
echo "🖥️ Backend API: http://localhost:3000"
echo "📊 Health Check: http://localhost:3000/api/options"
echo "📝 Logs: logs/backend.log, logs/frontend.log"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or use: pkill -f 'openhands.server.listen'"
echo "         pkill -f 'npm run start'"

# Save PIDs for later cleanup
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

echo ""
echo "✨ Setup complete! Open http://localhost:3001 in your browser"
EOF

# Make startup script executable
chmod +x startup.sh
```

## ✅ Verification & Testing

### 1. Health Check Endpoints
```bash
# Backend health check
curl -X GET http://localhost:3000/api/options

# DeepSeek integration test
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, test the DeepSeek integration",
    "model": "deepseek-r1-0528"
  }'

# Fallback mechanism test
curl -X POST http://localhost:3000/api/test-fallback \
  -H "Content-Type: application/json"
```

### 2. Frontend Verification
```bash
# Check if frontend is accessible
curl -I http://localhost:3001

# Test static assets
curl -I http://localhost:3001/static/js/main.js
```

### 3. Integration Test Script
```bash
#!/bin/bash
# test_integration.sh - Comprehensive integration testing

echo "🧪 Running OpenHands DeepSeek Integration Tests"
echo "==============================================="

# Test 1: Backend Health
echo "1. Testing backend health..."
if curl -f http://localhost:3000/api/options >/dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Test 2: Frontend Accessibility
echo "2. Testing frontend accessibility..."
if curl -f http://localhost:3001 >/dev/null 2>&1; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend accessibility check failed"
    exit 1
fi

# Test 3: DeepSeek Model Response
echo "3. Testing DeepSeek model response..."
RESPONSE=$(curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a simple Python hello world function",
    "model": "deepseek-r1-0528"
  }')

if echo "$RESPONSE" | grep -q "def\|print\|hello"; then
    echo "✅ DeepSeek model is responding correctly"
else
    echo "❌ DeepSeek model response test failed"
    echo "Response: $RESPONSE"
fi

# Test 4: Workspace Access
echo "4. Testing workspace access..."
if [ -d "/tmp/openhands_workspace" ] && [ -w "/tmp/openhands_workspace" ]; then
    echo "✅ Workspace is accessible and writable"
else
    echo "❌ Workspace access test failed"
fi

# Test 5: Log Files
echo "5. Checking log files..."
if [ -f "logs/backend.log" ] && [ -f "logs/frontend.log" ]; then
    echo "✅ Log files are being created"
    echo "Backend log size: $(wc -l < logs/backend.log) lines"
    echo "Frontend log size: $(wc -l < logs/frontend.log) lines"
else
    echo "❌ Log files not found"
fi

echo ""
echo "🎉 Integration tests completed!"
echo "Access your OpenHands instance at: http://localhost:3001"
EOF

chmod +x test_integration.sh
```

### 4. Sample Task Testing
```bash
# Create test task script
cat > test_tasks.py << 'EOF'
#!/usr/bin/env python3
"""
Sample tasks to test OpenHands with DeepSeek R1-0528
"""

import requests
import json
import time

BASE_URL = "http://localhost:3000"

def test_code_generation():
    """Test code generation capability"""
    print("🧪 Testing code generation...")
    
    payload = {
        "message": "Create a Python function that calculates the factorial of a number with error handling",
        "model": "deepseek-r1-0528",
        "max_tokens": 500
    }
    
    response = requests.post(f"{BASE_URL}/api/chat", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Code generation test passed")
        print(f"Response preview: {result.get('response', '')[:100]}...")
        return True
    else:
        print(f"❌ Code generation test failed: {response.status_code}")
        return False

def test_file_operations():
    """Test file system operations"""
    print("🧪 Testing file operations...")
    
    payload = {
        "message": "Create a new Python file called 'test_script.py' with a simple calculator function",
        "model": "deepseek-r1-0528",
        "workspace": "/tmp/openhands_workspace"
    }
    
    response = requests.post(f"{BASE_URL}/api/execute", json=payload)
    
    if response.status_code == 200:
        print("✅ File operations test passed")
        return True
    else:
        print(f"❌ File operations test failed: {response.status_code}")
        return False

def test_multi_turn_conversation():
    """Test multi-turn conversation capability"""
    print("🧪 Testing multi-turn conversation...")
    
    # First message
    payload1 = {
        "message": "I want to create a web scraper. What libraries should I use?",
        "model": "deepseek-r1-0528"
    }
    
    response1 = requests.post(f"{BASE_URL}/api/chat", json=payload1)
    
    if response1.status_code != 200:
        print(f"❌ First message failed: {response1.status_code}")
        return False
    
    # Follow-up message
    payload2 = {
        "message": "Now write the actual code for scraping a simple website",
        "model": "deepseek-r1-0528",
        "conversation_id": response1.json().get("conversation_id")
    }
    
    response2 = requests.post(f"{BASE_URL}/api/chat", json=payload2)
    
    if response2.status_code == 200:
        print("✅ Multi-turn conversation test passed")
        return True
    else:
        print(f"❌ Multi-turn conversation test failed: {response2.status_code}")
        return False

def test_fallback_mechanism():
    """Test fallback mechanism"""
    print("🧪 Testing fallback mechanism...")
    
    # Trigger fallback by using an invalid primary model
    payload = {
        "message": "Test fallback by using invalid model",
        "model": "invalid-model",
        "enable_fallback": True
    }
    
    response = requests.post(f"{BASE_URL}/api/chat", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if "fallback" in result.get("model_used", "").lower():
            print("✅ Fallback mechanism test passed")
            return True
    
    print("❌ Fallback mechanism test failed")
    return False

def main():
    """Run all tests"""
    print("🚀 Starting OpenHands DeepSeek Integration Tests")
    print("=" * 50)
    
    tests = [
        test_code_generation,
        test_file_operations,
        test_multi_turn_conversation,
        test_fallback_mechanism
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(2)  # Brief pause between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenHands with DeepSeek is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs for more details.")

if __name__ == "__main__":
    main()
EOF

chmod +x test_tasks.py
```

## 🔧 Development Workflow

### 1. Development Mode Setup
```bash
# Enable development mode
export DEBUG=true
export HOT_RELOAD=true
export LOG_LEVEL=DEBUG

# Start with auto-reload
python -m openhands.server.listen \
    --host 0.0.0.0 \
    --port 3000 \
    --reload \
    --config-file config.toml
```

### 2. Debug Configuration
```bash
# Create debug configuration
cat > debug_config.toml << 'EOF'
[core]
workspace_base = "/tmp/openhands_workspace"
max_iterations = 10  # Reduced for debugging
enable_auto_lint = false

[llm]
model = "deepseek-r1-0528"
api_key = "your-deepseek-api-key-here"
temperature = 0.1  # Lower temperature for consistent debugging
max_tokens = 1024  # Reduced for faster responses

[logging]
level = "DEBUG"
file = "logs/debug.log"
format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EOF
```

### 3. Hot Reload Setup
```bash
# Install development dependencies
pip install watchdog

# Create hot reload script
cat > hot_reload.py << 'EOF'
#!/usr/bin/env python3
import time
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_server()
    
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"🔄 File changed: {event.src_path}")
            self.restart_server()
    
    def restart_server(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        print("🚀 Starting server...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "openhands.server.listen",
            "--host", "0.0.0.0",
            "--port", "3000",
            "--config-file", "config.toml"
        ])

if __name__ == "__main__":
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, "openhands/", recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    
    observer.join()
EOF

chmod +x hot_reload.py
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Port Conflicts
```bash
# Check what's using the ports
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :3001

# Kill processes using the ports
sudo fuser -k 3000/tcp
sudo fuser -k 3001/tcp

# Alternative ports
export BACKEND_PORT=3002
export FRONTEND_PORT=3003
```

#### 2. Permission Issues
```bash
# Fix workspace permissions
sudo chown -R $USER:$USER /tmp/openhands_workspace
chmod -R 755 /tmp/openhands_workspace

# Fix log directory permissions
mkdir -p logs
chmod 755 logs
```

#### 3. DeepSeek API Issues
```bash
# Test DeepSeek API connectivity
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "model": "deepseek-r1-0528",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check API key validity
python3 -c "
import os
from openhands.llm.deepseek_r1 import create_deepseek_r1_llm
try:
    llm = create_deepseek_r1_llm(api_key='your-api-key-here')
    print('✅ DeepSeek API key is valid')
except Exception as e:
    print(f'❌ DeepSeek API key error: {e}')
"
```

#### 4. Frontend Build Issues
```bash
# Clear npm cache
cd frontend
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Build with verbose output
npm run build --verbose
```

#### 5. Memory Issues
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# Monitor memory usage
watch -n 1 'free -h && echo "---" && ps aux --sort=-%mem | head -10'
```

### Diagnostic Scripts
```bash
#!/bin/bash
# diagnose.sh - System diagnostic script

echo "🔍 OpenHands DeepSeek Diagnostic Report"
echo "======================================="

echo "📊 System Information:"
echo "OS: $(uname -a)"
echo "Python: $(python3 --version)"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h /tmp)"

echo ""
echo "🔌 Port Status:"
netstat -tulpn | grep -E ':(3000|3001)' || echo "Ports 3000/3001 are free"

echo ""
echo "📁 Directory Status:"
echo "Workspace: $(ls -la /tmp/openhands_workspace 2>/dev/null || echo 'Not found')"
echo "Logs: $(ls -la logs/ 2>/dev/null || echo 'Not found')"

echo ""
echo "🐍 Python Environment:"
python3 -c "
import sys
print(f'Python path: {sys.executable}')
try:
    import openhands
    print(f'OpenHands version: {openhands.__version__}')
except:
    print('OpenHands not installed')

try:
    from openhands.llm.deepseek_r1 import create_deepseek_r1_llm
    print('✅ DeepSeek integration available')
except Exception as e:
    print(f'❌ DeepSeek integration error: {e}')
"

echo ""
echo "📦 Node.js Environment:"
cd frontend 2>/dev/null && {
    echo "Frontend directory exists"
    echo "Package.json: $(test -f package.json && echo 'Found' || echo 'Missing')"
    echo "Node modules: $(test -d node_modules && echo 'Installed' || echo 'Missing')"
} || echo "Frontend directory not found"

echo ""
echo "🔧 Configuration:"
echo "Config file: $(test -f config.toml && echo 'Found' || echo 'Missing')"
echo "Environment file: $(test -f .env && echo 'Found' || echo 'Missing')"

echo ""
echo "📝 Recent Logs:"
if [ -f logs/backend.log ]; then
    echo "Backend log (last 5 lines):"
    tail -5 logs/backend.log
else
    echo "No backend log found"
fi

if [ -f logs/frontend.log ]; then
    echo "Frontend log (last 5 lines):"
    tail -5 logs/frontend.log
else
    echo "No frontend log found"
fi

echo ""
echo "🎯 Recommendations:"
if ! command -v docker >/dev/null 2>&1; then
    echo "⚠️ Consider installing Docker for containerized deployment"
fi

if [ ! -f .env ]; then
    echo "⚠️ Create .env file with your API keys"
fi

if [ ! -d /tmp/openhands_workspace ]; then
    echo "⚠️ Create workspace directory: mkdir -p /tmp/openhands_workspace"
fi

echo ""
echo "✅ Diagnostic complete!"
EOF

chmod +x diagnose.sh
```

## 🏭 Production Considerations

### 1. Security Configuration
```bash
# Create production environment file
cat > .env.production << 'EOF'
# Production Security Settings
DEBUG=false
HOT_RELOAD=false
LOG_LEVEL=WARNING

# Secure JWT secret (generate with: openssl rand -hex 32)
JWT_SECRET=your-secure-jwt-secret-here

# Restricted CORS origins
ALLOWED_ORIGINS=https://yourdomain.com

# Database encryption
DATABASE_ENCRYPTION_KEY=your-encryption-key-here

# API rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# SSL/TLS Configuration
USE_SSL=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
EOF
```

### 2. Performance Optimization
```bash
# Production startup script
cat > production_start.sh << 'EOF'
#!/bin/bash
# Production deployment script

# Set production environment
export NODE_ENV=production
export PYTHONOPTIMIZE=1

# Start with production settings
gunicorn openhands.server.listen:app \
    --bind 0.0.0.0:3000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 300 \
    --keep-alive 2 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level warning

# Serve frontend with nginx (recommended)
# nginx -c /path/to/nginx.conf
EOF

chmod +x production_start.sh
```

### 3. Monitoring Setup
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
# System monitoring script

while true; do
    echo "$(date): System Status Check"
    
    # Check backend health
    if curl -f http://localhost:3000/api/options >/dev/null 2>&1; then
        echo "✅ Backend healthy"
    else
        echo "❌ Backend unhealthy - restarting..."
        pkill -f "openhands.server.listen"
        sleep 5
        ./startup.sh
    fi
    
    # Check memory usage
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $MEM_USAGE -gt 90 ]; then
        echo "⚠️ High memory usage: ${MEM_USAGE}%"
    fi
    
    # Check disk space
    DISK_USAGE=$(df /tmp | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "⚠️ High disk usage: ${DISK_USAGE}%"
        # Cleanup old workspace files
        find /tmp/openhands_workspace -type f -mtime +7 -delete
    fi
    
    sleep 300  # Check every 5 minutes
done
EOF

chmod +x monitor.sh
```

## 🎯 Success Verification Checklist

### ✅ Pre-Launch Checklist
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Configuration files created
- [ ] Workspace directory accessible
- [ ] API keys valid and tested
- [ ] Ports available (3000, 3001)

### ✅ Launch Verification
- [ ] Backend starts without errors
- [ ] Frontend builds and serves successfully
- [ ] Health endpoints respond correctly
- [ ] DeepSeek integration functional
- [ ] Fallback mechanism working
- [ ] Workspace operations successful

### ✅ Functionality Tests
- [ ] Code generation works
- [ ] File operations successful
- [ ] Multi-turn conversations functional
- [ ] Error handling graceful
- [ ] Performance acceptable
- [ ] Logs being generated

## 🚀 Quick Start Commands

```bash
# Complete setup and launch (run these commands in order)
git clone <your-repo> && cd CodeAgent03
./startup.sh
./test_integration.sh

# Access the application
open http://localhost:3001

# Monitor logs
tail -f logs/backend.log logs/frontend.log

# Stop services
pkill -f "openhands.server.listen"
pkill -f "npm run start"
```

## 📞 Support and Resources

### Documentation
- [OpenHands Documentation](https://docs.all-hands.dev)
- [DeepSeek API Documentation](https://api-docs.deepseek.com)
- [Integration Guide](./DEEPSEEK_INTEGRATION_PLAN.md)

### Troubleshooting
- Check logs in `logs/` directory
- Run `./diagnose.sh` for system analysis
- Verify API keys and network connectivity
- Ensure all dependencies are installed

### Community
- [OpenHands GitHub Issues](https://github.com/All-Hands-AI/OpenHands/issues)
- [DeepSeek Community](https://github.com/deepseek-ai)

---

🎉 **Congratulations!** You now have a fully functional OpenHands installation with DeepSeek R1-0528 integration running locally. The system provides cost-effective AI software engineering capabilities with intelligent fallback mechanisms and comprehensive monitoring.