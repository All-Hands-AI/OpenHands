#!/bin/bash
# startup.sh - Complete OpenHands with DeepSeek startup script

set -e

echo "🚀 Starting OpenHands with DeepSeek R1-0528 Integration"
echo "======================================================="

# Create environment variables
cat > .env << 'EOF'
# OpenHands with DeepSeek R1-0528 Configuration
LLM_MODEL=deepseek-r1-0528
LLM_API_KEY=demo-key-for-testing
LLM_BASE_URL=https://api.deepseek.com
LLM_PROVIDER=deepseek
ENABLE_FALLBACK=true
FALLBACK_MODELS=deepseek-r1-0528,gpt-3.5-turbo
AUTO_FALLBACK_ON_ERROR=true
SANDBOX_TYPE=local
WORKSPACE_BASE=/tmp/openhands_workspace
MAX_ITERATIONS=100
MAX_BUDGET_PER_TASK=10.0
BACKEND_HOST=0.0.0.0
BACKEND_PORT=3000
FRONTEND_PORT=3001
JWT_SECRET=demo-jwt-secret-for-testing
ALLOWED_ORIGINS=http://localhost:3001,http://127.0.0.1:3001
DATABASE_URL=sqlite:///./openhands.db
LOG_LEVEL=INFO
LOG_FILE=/tmp/openhands.log
DEBUG=true
HOT_RELOAD=true
DOCKER_ENABLED=false
MAX_CONCURRENT_SESSIONS=5
REQUEST_TIMEOUT=300
RESPONSE_CACHE_TTL=3600
DEEPSEEK_MODEL_PATH=deepseek-ai/DeepSeek-R1-0528
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_TOP_P=0.9
ENABLE_COST_TRACKING=true
MAX_COST_PER_SESSION=5.0
COST_ALERT_THRESHOLD=3.0
EOF

# Load environment variables
source .env
export $(cat .env | grep -v '^#' | xargs)
echo "✅ Environment variables loaded"

# Check dependencies
echo "🔍 Checking dependencies..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required but not installed."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm required but not installed."; exit 1; }
echo "✅ All dependencies found"

# Create workspace and logs
echo "📁 Setting up workspace..."
mkdir -p /tmp/openhands_workspace
mkdir -p logs
chmod 755 /tmp/openhands_workspace
echo "✅ Workspace created"

# Create configuration file
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
api_key = "demo-key-for-testing"
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
enable_fallback = true
fallback_models = ["deepseek-r1-0528", "gpt-3.5-turbo"]
auto_fallback_on_error = true
fallback_retry_attempts = 3
fallback_cooldown_period = 300

[llm.fallback_api_keys]
"deepseek-r1-0528" = "demo-key-for-testing"
"gpt-3.5-turbo" = "demo-key-for-testing"

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

echo "✅ Configuration file created"

# Install Python dependencies if needed
echo "🐍 Checking Python dependencies..."
if ! python3 -c "import openhands" 2>/dev/null; then
    echo "Installing Python dependencies..."
    if command -v poetry >/dev/null 2>&1; then
        poetry install --no-dev
    else
        pip install -e .
    fi
fi
echo "✅ Python dependencies ready"

# Install frontend dependencies if needed
echo "📦 Checking frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
cd ..
echo "✅ Frontend dependencies ready"

# Kill any existing processes on our ports
echo "🧹 Cleaning up existing processes..."
pkill -f "openhands.server.listen" 2>/dev/null || true
pkill -f "npm run start" 2>/dev/null || true
sleep 2

# Start backend in background
echo "🖥️ Starting backend server..."
python3 -m openhands.server.listen \
    --host 0.0.0.0 \
    --port 3000 \
    --file-store-path /tmp/openhands_workspace \
    --config-file config.toml > logs/backend.log 2>&1 &

BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
for i in {1..30}; do
    if curl -f http://localhost:3000/api/options >/dev/null 2>&1; then
        echo "✅ Backend is responding"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start within 30 seconds"
        echo "Backend log:"
        tail -20 logs/backend.log
        exit 1
    fi
    sleep 1
done

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
echo "🧪 Run './test_integration.sh' to verify everything is working"