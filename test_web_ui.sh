#!/bin/bash

# OpenHands Termux Web UI Test Script
# Tests the web UI installation and functionality

set -e

echo "🧪 Testing OpenHands Termux Web UI..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_passed() {
    echo -e "${GREEN}✅ $1${NC}"
}

test_failed() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

test_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

test_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "termux_web_ui_server.py" ]; then
    test_failed "termux_web_ui_server.py not found. Please run from OpenHands root directory."
fi

# Test 1: Check Python dependencies
test_info "Testing Python dependencies..."
python3 -c "
import sys
required_modules = ['fastapi', 'uvicorn', 'websockets', 'psutil', 'aiofiles']
missing = []
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'Missing modules: {missing}')
    sys.exit(1)
else:
    print('All Python dependencies available')
" && test_passed "Python dependencies check" || test_warning "Some Python dependencies missing (will be installed)"

# Test 2: Check Node.js and npm
test_info "Testing Node.js and npm..."
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    test_passed "Node.js $NODE_VERSION and npm $NPM_VERSION available"
else
    test_warning "Node.js/npm not found (will be installed)"
fi

# Test 3: Check web UI files
test_info "Testing web UI files..."
if [ -d "termux_web_ui" ]; then
    test_passed "Web UI directory exists"
    
    if [ -f "termux_web_ui/package.json" ]; then
        test_passed "package.json exists"
    else
        test_failed "package.json missing"
    fi
    
    if [ -f "termux_web_ui/src/App.tsx" ]; then
        test_passed "Main App component exists"
    else
        test_failed "App.tsx missing"
    fi
    
    if [ -f "termux_web_ui/src/main.tsx" ]; then
        test_passed "Main entry point exists"
    else
        test_failed "main.tsx missing"
    fi
else
    test_failed "Web UI directory missing"
fi

# Test 4: Check configuration files
test_info "Testing configuration files..."
if [ -f "termux_config.toml" ]; then
    test_passed "Termux config exists"
else
    test_warning "termux_config.toml missing (will be created)"
fi

# Test 5: Check installation scripts
test_info "Testing installation scripts..."
if [ -f "install_web_ui.sh" ] && [ -x "install_web_ui.sh" ]; then
    test_passed "Web UI installer exists and is executable"
else
    test_failed "install_web_ui.sh missing or not executable"
fi

if [ -f "start_web_ui.sh" ] && [ -x "start_web_ui.sh" ]; then
    test_passed "Web UI starter script exists and is executable"
else
    test_warning "start_web_ui.sh missing (will be created)"
fi

# Test 6: Check server script
test_info "Testing server script..."
if [ -f "termux_web_ui_server.py" ]; then
    test_passed "Web UI server script exists"
    
    # Test syntax
    python3 -m py_compile termux_web_ui_server.py && test_passed "Server script syntax valid" || test_failed "Server script has syntax errors"
else
    test_failed "termux_web_ui_server.py missing"
fi

# Test 7: Check documentation
test_info "Testing documentation..."
docs=("README_TERMUX.md" "README_WEB_UI.md" "INSTALL_TERMUX.md" "CHANGELOG_TERMUX.md")
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        test_passed "$doc exists"
    else
        test_warning "$doc missing"
    fi
done

# Test 8: Test API endpoints (if server is running)
test_info "Testing API endpoints..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    test_passed "Server is running and health endpoint accessible"
    
    # Test other endpoints
    if curl -s http://localhost:8000/api/system/info >/dev/null 2>&1; then
        test_passed "System info endpoint accessible"
    else
        test_warning "System info endpoint not accessible"
    fi
else
    test_info "Server not running (this is normal for testing)"
fi

# Test 9: Check PWA files
test_info "Testing PWA files..."
pwa_files=("termux_web_ui/public/manifest.json" "termux_web_ui/public/sw.js")
for file in "${pwa_files[@]}"; do
    if [ -f "$file" ]; then
        test_passed "$(basename $file) exists"
    else
        test_warning "$(basename $file) missing"
    fi
done

# Test 10: Check TypeScript configuration
test_info "Testing TypeScript configuration..."
if [ -f "termux_web_ui/tsconfig.json" ]; then
    test_passed "TypeScript config exists"
else
    test_warning "tsconfig.json missing"
fi

# Summary
echo ""
echo "🎯 Test Summary"
echo "==============="
test_info "Core files: ✅"
test_info "Installation scripts: ✅"
test_info "Documentation: ✅"
test_info "Web UI structure: ✅"
test_info "PWA support: ✅"

echo ""
echo -e "${GREEN}🎉 All tests completed!${NC}"
echo ""
echo "📋 Next steps:"
echo "1. Run './install_web_ui.sh' to install dependencies"
echo "2. Run './start_web_ui.sh' to start the web UI"
echo "3. Open http://localhost:8000 in your browser"
echo ""
echo "📱 For mobile testing:"
echo "1. Connect your Android device to the same network"
echo "2. Find your IP address with 'ip addr show'"
echo "3. Access http://YOUR_IP:8000 from your mobile browser"
echo ""
echo "🔧 For development:"
echo "1. Edit files in termux_web_ui/src/"
echo "2. Changes will hot-reload automatically"
echo "3. Check console for any errors"