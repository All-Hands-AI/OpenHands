#!/bin/bash
# Quick Start Script for DeepSeek R1-0528 Local Deployment
# No API keys required - completely local!

set -e

echo "🤖 DeepSeek R1-0528 Quick Start"
echo "==============================="
echo "Setting up local DeepSeek R1-0528 server..."
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check pip
if ! command_exists pip; then
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "✓ pip available"

# Install vLLM and dependencies
echo "📦 Installing vLLM and dependencies..."
pip install --upgrade pip

# Install PyTorch (CPU version for compatibility)
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install vLLM
echo "Installing vLLM..."
pip install vllm

# Install additional dependencies
echo "Installing additional dependencies..."
pip install transformers accelerate requests

echo "✅ Dependencies installed!"

# Check GPU availability
echo
echo "🔍 Checking GPU availability..."
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'✓ CUDA available: {torch.version.cuda}')
    print(f'✓ GPU: {torch.cuda.get_device_name()}')
    print('Will use GPU acceleration')
else:
    print('⚠ CUDA not available - will use CPU mode')
    print('Note: CPU mode will be slower but still functional')
"

echo
echo "🚀 Starting DeepSeek R1-0528 server..."
echo "This will download the model on first run (~50GB)"
echo "Please be patient..."

# Start the server
echo
echo "Command that will be executed:"
echo "vllm serve 'deepseek-ai/DeepSeek-R1-0528' --host 0.0.0.0 --port 8000 --trust-remote-code"
echo

# Check if user wants to continue
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 1
fi

# Start vLLM server
echo "Starting server..."
vllm serve "deepseek-ai/DeepSeek-R1-0528" \
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 10

# Test server
echo "🧪 Testing server..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Server is ready!"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 5
done

# Test with a simple request
echo
echo "🧪 Testing with a simple request..."
curl -X POST "http://localhost:8000/v1/chat/completions" \
    -H "Content-Type: application/json" \
    --data '{
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ],
        "max_tokens": 50
    }' | python3 -m json.tool

echo
echo "🎉 DeepSeek R1-0528 is now running locally!"
echo "========================================"
echo
echo "API Endpoint: http://localhost:8000/v1/chat/completions"
echo "Health Check: http://localhost:8000/health"
echo "Server PID: $SERVER_PID"
echo
echo "Example usage:"
echo "curl -X POST \"http://localhost:8000/v1/chat/completions\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    --data '{"
echo "        \"model\": \"deepseek-ai/DeepSeek-R1-0528\","
echo "        \"messages\": ["
echo "            {"
echo "                \"role\": \"user\","
echo "                \"content\": \"Your question here\""
echo "            }"
echo "        ]"
echo "    }'"
echo
echo "To stop the server: kill $SERVER_PID"
echo "Or press Ctrl+C to stop this script"

# Keep script running
echo
echo "Press Ctrl+C to stop the server..."
wait $SERVER_PID