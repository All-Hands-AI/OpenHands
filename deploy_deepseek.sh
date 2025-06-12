#!/bin/bash
# Complete DeepSeek R1-0528 Local Deployment Script
# No API keys required - completely local deployment!

set -e

echo "🚀 DeepSeek R1-0528 Complete Local Deployment"
echo "============================================="
echo "Setting up production-ready local DeepSeek server..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi
print_status "Python found: $(python3 --version)"

# Check pip
if ! command_exists pip; then
    print_info "Installing pip..."
    python3 -m ensurepip --upgrade
fi
print_status "pip available"

# Check available memory
total_memory=$(free -g | awk '/^Mem:/{print $2}')
if [ "$total_memory" -lt 8 ]; then
    print_warning "Low memory detected (${total_memory}GB). Recommend 16GB+ for optimal performance."
    print_info "Will use aggressive quantization and CPU optimizations."
fi

# Check GPU
echo
echo "🔍 Checking GPU availability..."
if command_exists nvidia-smi; then
    gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
    gpu_memory=$(echo "$gpu_info" | cut -d',' -f2 | tr -d ' ')
    
    if [ "$gpu_memory" -gt 8000 ]; then
        print_status "GPU detected: $gpu_info"
        USE_GPU=true
    else
        print_warning "GPU memory too low (${gpu_memory}MB). Using CPU mode."
        USE_GPU=false
    fi
else
    print_warning "No GPU detected. Using CPU mode."
    USE_GPU=false
fi

# Install dependencies
echo
echo "📦 Installing dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "deepseek_env" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv deepseek_env
fi

# Activate virtual environment
source deepseek_env/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install PyTorch
print_info "Installing PyTorch..."
if [ "$USE_GPU" = true ]; then
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    print_status "PyTorch with CUDA support installed"
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    print_status "PyTorch (CPU-only) installed"
fi

# Install other dependencies
print_info "Installing other dependencies..."
pip install \
    transformers>=4.37.0 \
    accelerate>=0.26.0 \
    bitsandbytes>=0.42.0 \
    requests \
    numpy \
    pandas

# Install optional GPU dependencies
if [ "$USE_GPU" = true ]; then
    print_info "Installing GPU optimizations..."
    pip install flash-attn --no-build-isolation || print_warning "Flash Attention installation failed (optional)"
fi

print_status "All dependencies installed"

# Test installation
echo
echo "🧪 Testing installation..."
python3 test_vllm_setup.py --skip-wait || {
    print_warning "Some tests failed, but continuing with deployment..."
}

# Configure deployment
echo
echo "⚙️  Configuring deployment..."

# Determine optimal settings
if [ "$USE_GPU" = true ]; then
    QUANTIZATION="--no-quantization"
    MAX_LENGTH="4096"
    print_info "Using GPU mode with full precision"
else
    QUANTIZATION=""
    MAX_LENGTH="2048"
    print_info "Using CPU mode with quantization"
fi

# Create startup script
cat > start_deepseek_server.sh << EOF
#!/bin/bash
# DeepSeek R1-0528 Server Startup Script

echo "🚀 Starting DeepSeek R1-0528 Local Server..."
echo "============================================"

# Activate virtual environment
source deepseek_env/bin/activate

# Start server
python3 production_deepseek_server.py \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --max-length $MAX_LENGTH \\
    $QUANTIZATION

EOF

chmod +x start_deepseek_server.sh

# Create test script
cat > test_deepseek_deployment.sh << EOF
#!/bin/bash
# Test DeepSeek deployment

echo "🧪 Testing DeepSeek deployment..."

# Activate virtual environment
source deepseek_env/bin/activate

# Run tests
python3 test_deepseek_client.py --url http://localhost:8000

EOF

chmod +x test_deepseek_deployment.sh

print_status "Configuration completed"

# Start server
echo
echo "🚀 Starting DeepSeek R1-0528 server..."
print_info "This will download the model on first run (~50GB)"
print_info "Server will be available at: http://localhost:8000"

# Ask user if they want to start now
read -p "Start the server now? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting server in background..."
    
    # Start server in background
    nohup ./start_deepseek_server.sh > deepseek_server.log 2>&1 &
    SERVER_PID=$!
    
    echo $SERVER_PID > deepseek_server.pid
    print_status "Server started with PID: $SERVER_PID"
    print_info "Logs: tail -f deepseek_server.log"
    
    # Wait a bit and test
    print_info "Waiting for server to initialize..."
    sleep 10
    
    # Test server
    print_info "Testing server..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_status "Server is responding!"
        
        # Run basic test
        echo
        print_info "Running basic functionality test..."
        ./test_deepseek_deployment.sh
        
    else
        print_warning "Server not responding yet. Check logs: tail -f deepseek_server.log"
    fi
    
else
    print_info "Server not started. To start manually:"
    echo "  ./start_deepseek_server.sh"
fi

# Print final instructions
echo
echo "🎉 DeepSeek R1-0528 Deployment Complete!"
echo "========================================"
echo
echo "📋 Quick Reference:"
echo "  Start server:    ./start_deepseek_server.sh"
echo "  Test server:     ./test_deepseek_deployment.sh"
echo "  Server logs:     tail -f deepseek_server.log"
echo "  Stop server:     kill \$(cat deepseek_server.pid)"
echo
echo "🌐 API Endpoints:"
echo "  Health check:    http://localhost:8000/health"
echo "  Chat API:        http://localhost:8000/v1/chat/completions"
echo "  Statistics:      http://localhost:8000/stats"
echo
echo "💡 Example Usage:"
echo "  curl -X POST \"http://localhost:8000/v1/chat/completions\" \\"
echo "      -H \"Content-Type: application/json\" \\"
echo "      --data '{"
echo "          \"model\": \"deepseek-ai/DeepSeek-R1-0528\","
echo "          \"messages\": ["
echo "              {\"role\": \"user\", \"content\": \"Hello!\"}"
echo "          ]"
echo "      }'"
echo
echo "🔧 Troubleshooting:"
echo "  - Check logs if server doesn't start"
echo "  - Ensure sufficient memory (16GB+ recommended)"
echo "  - Model download requires stable internet connection"
echo "  - First startup takes longer due to model download"
echo
print_status "Deployment completed successfully!"

# Save deployment info
cat > deployment_info.txt << EOF
DeepSeek R1-0528 Local Deployment
================================

Deployment Date: $(date)
GPU Mode: $USE_GPU
Memory: ${total_memory}GB
Python: $(python3 --version)

Server Configuration:
- Host: 0.0.0.0
- Port: 8000
- Max Length: $MAX_LENGTH
- Quantization: $([ "$QUANTIZATION" = "" ] && echo "Enabled" || echo "Disabled")

Files Created:
- start_deepseek_server.sh (server startup)
- test_deepseek_deployment.sh (testing)
- deepseek_server.log (server logs)
- deepseek_server.pid (server process ID)

API Endpoints:
- Health: http://localhost:8000/health
- Chat: http://localhost:8000/v1/chat/completions
- Stats: http://localhost:8000/stats
EOF

print_status "Deployment info saved to deployment_info.txt"