#!/bin/bash

# OpenHands + Ollama Health Check Script
# This script verifies that your setup is working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  OpenHands + Ollama Health Check${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check Docker
check_docker() {
    print_status "Checking Docker..."
    if docker info >/dev/null 2>&1; then
        print_success "Docker is running"
        DOCKER_VERSION=$(docker --version)
        echo "    Version: $DOCKER_VERSION"
    else
        print_error "Docker is not running or not accessible"
        return 1
    fi
}

# Check Ollama connectivity
check_ollama() {
    print_status "Checking Ollama connectivity..."

    OLLAMA_URLS=("http://localhost:11434" "http://127.0.0.1:11434")
    OLLAMA_FOUND=false

    for url in "${OLLAMA_URLS[@]}"; do
        if curl -s --connect-timeout 5 "$url/api/tags" >/dev/null 2>&1; then
            print_success "Ollama is accessible at $url"
            OLLAMA_URL="$url"
            OLLAMA_FOUND=true
            break
        fi
    done

    if [ "$OLLAMA_FOUND" = false ]; then
        print_error "Ollama is not accessible"
        echo "    Please ensure Ollama is running: ollama serve"
        return 1
    fi
}

# Check Ollama models
check_ollama_models() {
    print_status "Checking Ollama models..."

    if [ -z "$OLLAMA_URL" ]; then
        print_error "Ollama URL not set"
        return 1
    fi

    MODELS_JSON=$(curl -s "$OLLAMA_URL/api/tags" 2>/dev/null || echo '{"models":[]}')
    MODELS=$(echo "$MODELS_JSON" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [ -z "$MODELS" ]; then
        print_warning "No models found in Ollama"
        return 1
    fi

    echo "    Available models:"
    echo "$MODELS" | while read -r model; do
        echo "      - $model"
    done

    # Check for specific DeepSeek models
    DEEPSEEK_CODER_FOUND=false
    DEEPSEEK_R1_FOUND=false

    if echo "$MODELS" | grep -q "deepseek-coder-v2:latest"; then
        DEEPSEEK_CODER_FOUND=true
        print_success "Found deepseek-coder-v2:latest"
    else
        print_warning "deepseek-coder-v2:latest not found"
        echo "    Run: ollama pull deepseek-coder-v2:latest"
    fi

    if echo "$MODELS" | grep -q "deepseek-r1:14b"; then
        DEEPSEEK_R1_FOUND=true
        print_success "Found deepseek-r1:14b"
    else
        print_warning "deepseek-r1:14b not found"
        echo "    Run: ollama pull deepseek-r1:14b"
    fi

    if [ "$DEEPSEEK_CODER_FOUND" = true ] || [ "$DEEPSEEK_R1_FOUND" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test Ollama model response
test_ollama_model() {
    print_status "Testing Ollama model response..."

    # Find an available DeepSeek model
    MODELS_JSON=$(curl -s "$OLLAMA_URL/api/tags" 2>/dev/null || echo '{"models":[]}')
    MODELS=$(echo "$MODELS_JSON" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    TEST_MODEL=""
    if echo "$MODELS" | grep -q "deepseek-coder-v2:latest"; then
        TEST_MODEL="deepseek-coder-v2:latest"
    elif echo "$MODELS" | grep -q "deepseek-r1:14b"; then
        TEST_MODEL="deepseek-r1:14b"
    fi

    if [ -z "$TEST_MODEL" ]; then
        print_warning "No DeepSeek models available for testing"
        return 1
    fi

    print_status "Testing model: $TEST_MODEL"

    # Test with a simple prompt
    TEST_PROMPT='{"model":"'$TEST_MODEL'","prompt":"Hello! Please respond with just: Working","stream":false}'

    RESPONSE=$(curl -s --connect-timeout 30 -X POST "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "$TEST_PROMPT" 2>/dev/null || echo "")

    if [ -n "$RESPONSE" ] && echo "$RESPONSE" | grep -q "Working"; then
        print_success "Model $TEST_MODEL is responding correctly"
    elif [ -n "$RESPONSE" ]; then
        print_warning "Model $TEST_MODEL responded, but output may be unexpected"
        echo "    Response: $(echo "$RESPONSE" | head -c 100)..."
    else
        print_error "Model $TEST_MODEL did not respond"
        return 1
    fi
}

# Check OpenHands Docker container
check_openhands_container() {
    print_status "Checking OpenHands container..."

    if docker ps --format "table {{.Names}}" | grep -q "openhands-ollama"; then
        print_success "OpenHands container is running"

        # Check if the service is responding
        if curl -s --connect-timeout 10 "http://localhost:3000" >/dev/null 2>&1; then
            print_success "OpenHands web interface is accessible at http://localhost:3000"
        else
            print_warning "OpenHands container is running but web interface is not accessible"
            echo "    It may still be starting up. Wait a moment and try again."
        fi
    else
        print_warning "OpenHands container is not running"
        echo "    Run: ./start-ollama.sh"
        return 1
    fi
}

# Check configuration files
check_config_files() {
    print_status "Checking configuration files..."

    if [ -f "config.toml" ]; then
        print_success "config.toml found"
    else
        print_error "config.toml not found"
        return 1
    fi

    if [ -f "docker-compose.ollama.yml" ]; then
        print_success "docker-compose.ollama.yml found"
    else
        print_error "docker-compose.ollama.yml not found"
        return 1
    fi

    if [ -f "start-ollama.sh" ]; then
        print_success "start-ollama.sh found"
    else
        print_error "start-ollama.sh not found"
        return 1
    fi
}

# Check workspace
check_workspace() {
    print_status "Checking workspace..."

    if [ -d "workspace" ]; then
        print_success "Workspace directory exists"
    else
        print_warning "Workspace directory not found"
        echo "    Creating workspace directory..."
        mkdir -p workspace
        print_success "Workspace directory created"
    fi

    if [ -d "$HOME/.openhands" ]; then
        print_success "OpenHands config directory exists"
    else
        print_warning "OpenHands config directory not found"
        echo "    Creating OpenHands config directory..."
        mkdir -p "$HOME/.openhands"
        print_success "OpenHands config directory created"
    fi
}

# Main health check
main() {
    print_header

    CHECKS_PASSED=0
    TOTAL_CHECKS=7

    check_docker && ((CHECKS_PASSED++)) || true
    check_ollama && ((CHECKS_PASSED++)) || true
    check_ollama_models && ((CHECKS_PASSED++)) || true
    test_ollama_model && ((CHECKS_PASSED++)) || true
    check_config_files && ((CHECKS_PASSED++)) || true
    check_workspace && ((CHECKS_PASSED++)) || true
    check_openhands_container && ((CHECKS_PASSED++)) || true

    echo
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Health Check Summary${NC}"
    echo -e "${BLUE}================================${NC}"

    if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
        print_success "All checks passed! ($CHECKS_PASSED/$TOTAL_CHECKS)"
        echo
        echo -e "${GREEN}🎉 Your OpenHands + Ollama setup is working perfectly!${NC}"
        echo -e "${GREEN}   Access OpenHands at: http://localhost:3000${NC}"
    elif [ $CHECKS_PASSED -gt $((TOTAL_CHECKS / 2)) ]; then
        print_warning "Most checks passed ($CHECKS_PASSED/$TOTAL_CHECKS)"
        echo
        echo -e "${YELLOW}⚠️  Your setup is mostly working, but some issues need attention.${NC}"
    else
        print_error "Several checks failed ($CHECKS_PASSED/$TOTAL_CHECKS)"
        echo
        echo -e "${RED}❌ Your setup needs attention before it will work properly.${NC}"
    fi

    echo
    echo "For help, see OLLAMA_SETUP.md or run: ./start-ollama.sh"
}

main "$@"
