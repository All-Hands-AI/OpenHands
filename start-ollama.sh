#!/bin/bash

# OpenHands with Local Ollama DeepSeek Models Setup Script
# This script helps you set up and run OpenHands with your local Ollama instance

set -e

echo "🚀 OpenHands + Local Ollama DeepSeek Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    print_status "Checking Docker..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Ollama is accessible
check_ollama() {
    print_status "Checking Ollama connection..."

    # Try different common Ollama URLs
    OLLAMA_URLS=("http://localhost:11434" "http://127.0.0.1:11434" "http://host.docker.internal:11434")
    OLLAMA_ACCESSIBLE=false

    for url in "${OLLAMA_URLS[@]}"; do
        if curl -s "$url/api/tags" >/dev/null 2>&1; then
            print_success "Ollama is accessible at $url"
            OLLAMA_ACCESSIBLE=true
            OLLAMA_BASE_URL="$url"
            break
        fi
    done

    if [ "$OLLAMA_ACCESSIBLE" = false ]; then
        print_error "Cannot connect to Ollama. Please ensure:"
        echo "  1. Ollama is running (ollama serve)"
        echo "  2. Ollama is accessible on port 11434"
        echo "  3. If running on a different machine, update the config.toml file"
        exit 1
    fi
}

# Check if required models are available
check_models() {
    print_status "Checking available Ollama models..."

    # Get list of models from Ollama
    MODELS=$(curl -s "$OLLAMA_BASE_URL/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [ -z "$MODELS" ]; then
        print_error "Could not retrieve models from Ollama"
        exit 1
    fi

    echo "Available models:"
    echo "$MODELS" | while read -r model; do
        echo "  - $model"
    done

    # Check for DeepSeek models
    DEEPSEEK_CODER_FOUND=false
    DEEPSEEK_R1_FOUND=false

    if echo "$MODELS" | grep -q "deepseek-coder-v2:latest"; then
        DEEPSEEK_CODER_FOUND=true
        print_success "Found deepseek-coder-v2:latest"
    fi

    if echo "$MODELS" | grep -q "deepseek-r1:14b"; then
        DEEPSEEK_R1_FOUND=true
        print_success "Found deepseek-r1:14b"
    fi

    if [ "$DEEPSEEK_CODER_FOUND" = false ] && [ "$DEEPSEEK_R1_FOUND" = false ]; then
        print_warning "Neither deepseek-coder-v2:latest nor deepseek-r1:14b found in Ollama"
        echo "To pull the models, run:"
        echo "  ollama pull deepseek-coder-v2:latest"
        echo "  ollama pull deepseek-r1:14b"
        echo ""
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create workspace directory
setup_workspace() {
    print_status "Setting up workspace..."
    mkdir -p workspace
    mkdir -p ~/.openhands
    print_success "Workspace created"
}

# Build OpenHands Docker image
build_image() {
    print_status "Building OpenHands Docker image..."
    docker-compose -f docker-compose.ollama.yml build
    print_success "Docker image built successfully"
}

# Start OpenHands
start_openhands() {
    print_status "Starting OpenHands with Ollama..."

    # Stop any existing containers
    docker-compose -f docker-compose.ollama.yml down 2>/dev/null || true

    # Start the service
    docker-compose -f docker-compose.ollama.yml up -d

    print_success "OpenHands started successfully!"
    echo ""
    echo "🌐 Access OpenHands at: http://localhost:3000"
    echo ""
    echo "📋 Configuration:"
    echo "  - Primary Model: ollama/deepseek-coder-v2:latest"
    echo "  - Alternative Model: ollama/deepseek-r1:14b"
    echo "  - Ollama URL: $OLLAMA_BASE_URL"
    echo ""
    echo "📝 To view logs: docker-compose -f docker-compose.ollama.yml logs -f"
    echo "🛑 To stop: docker-compose -f docker-compose.ollama.yml down"
}

# Main execution
main() {
    check_docker
    check_ollama
    check_models
    setup_workspace
    build_image
    start_openhands
}

# Handle script arguments
case "${1:-}" in
    "stop")
        print_status "Stopping OpenHands..."
        docker-compose -f docker-compose.ollama.yml down
        print_success "OpenHands stopped"
        ;;
    "logs")
        docker-compose -f docker-compose.ollama.yml logs -f
        ;;
    "restart")
        print_status "Restarting OpenHands..."
        docker-compose -f docker-compose.ollama.yml restart
        print_success "OpenHands restarted"
        ;;
    "rebuild")
        print_status "Rebuilding and restarting OpenHands..."
        docker-compose -f docker-compose.ollama.yml down
        docker-compose -f docker-compose.ollama.yml build --no-cache
        docker-compose -f docker-compose.ollama.yml up -d
        print_success "OpenHands rebuilt and restarted"
        ;;
    *)
        main
        ;;
esac
