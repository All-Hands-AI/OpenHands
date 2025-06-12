#!/bin/bash
# diagnose.sh - System diagnostic script

echo "🔍 OpenHands DeepSeek Diagnostic Report"
echo "======================================="
echo "Generated: $(date)"
echo ""

echo "📊 System Information:"
echo "OS: $(uname -a)"
echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "Node.js: $(node --version 2>/dev/null || echo 'Not found')"
echo "npm: $(npm --version 2>/dev/null || echo 'Not found')"
echo "Memory: $(free -h 2>/dev/null | grep Mem || echo 'Memory info not available')"
echo "Disk: $(df -h /tmp 2>/dev/null | tail -1 || echo 'Disk info not available')"

echo ""
echo "🔌 Port Status:"
netstat -tulpn 2>/dev/null | grep -E ':(3000|3001)' || echo "Ports 3000/3001 are free"

echo ""
echo "📁 Directory Status:"
echo "Current directory: $(pwd)"
echo "Workspace: $(ls -la /tmp/openhands_workspace 2>/dev/null || echo 'Not found')"
echo "Logs directory: $(ls -la logs/ 2>/dev/null || echo 'Not found')"
echo "Frontend directory: $(ls -la frontend/ 2>/dev/null | head -3 || echo 'Not found')"

echo ""
echo "🐍 Python Environment:"
python3 -c "
import sys
print(f'Python executable: {sys.executable}')
print(f'Python path: {sys.path[0]}')

try:
    import openhands
    print('✅ OpenHands package available')
    try:
        print(f'OpenHands location: {openhands.__file__}')
    except:
        pass
except ImportError as e:
    print(f'❌ OpenHands package not found: {e}')

try:
    from openhands.llm.deepseek_r1 import create_deepseek_r1_llm
    print('✅ DeepSeek integration available')
except ImportError as e:
    print(f'❌ DeepSeek integration not found: {e}')

try:
    from openhands.llm.enhanced_llm import EnhancedLLM
    print('✅ Enhanced LLM available')
except ImportError as e:
    print(f'❌ Enhanced LLM not found: {e}')

try:
    from openhands.core.config.llm_config import LLMConfig
    print('✅ LLM Config available')
except ImportError as e:
    print(f'❌ LLM Config not found: {e}')

# Check installed packages
try:
    import pkg_resources
    installed_packages = [d.project_name for d in pkg_resources.working_set]
    openhands_related = [p for p in installed_packages if 'openhands' in p.lower()]
    if openhands_related:
        print(f'OpenHands packages: {openhands_related}')
except:
    pass
"

echo ""
echo "📦 Node.js Environment:"
if [ -d "frontend" ]; then
    cd frontend 2>/dev/null && {
        echo "✅ Frontend directory exists"
        echo "Package.json: $(test -f package.json && echo 'Found' || echo 'Missing')"
        echo "Node modules: $(test -d node_modules && echo 'Installed' || echo 'Missing')"
        if [ -f package.json ]; then
            echo "Package.json scripts:"
            node -e "
                try {
                    const pkg = require('./package.json');
                    console.log('  Available scripts:', Object.keys(pkg.scripts || {}).join(', '));
                } catch(e) {
                    console.log('  Error reading package.json:', e.message);
                }
            " 2>/dev/null || echo "  Could not read package.json"
        fi
        cd ..
    } || echo "❌ Could not access frontend directory"
else
    echo "❌ Frontend directory not found"
fi

echo ""
echo "🔧 Configuration Files:"
echo "Config file (config.toml): $(test -f config.toml && echo 'Found' || echo 'Missing')"
echo "Environment file (.env): $(test -f .env && echo 'Found' || echo 'Missing')"
echo "Startup script: $(test -f startup.sh && echo 'Found' || echo 'Missing')"
echo "Test script: $(test -f test_integration.sh && echo 'Found' || echo 'Missing')"

if [ -f config.toml ]; then
    echo ""
    echo "Configuration preview:"
    head -10 config.toml | sed 's/^/  /'
fi

echo ""
echo "🏃 Process Status:"
if command -v pgrep >/dev/null 2>&1; then
    OPENHANDS_PROCS=$(pgrep -f "openhands.server.listen" 2>/dev/null || echo "")
    NPM_PROCS=$(pgrep -f "npm run start" 2>/dev/null || echo "")
    
    if [ -n "$OPENHANDS_PROCS" ]; then
        echo "✅ OpenHands backend processes: $OPENHANDS_PROCS"
    else
        echo "❌ No OpenHands backend processes found"
    fi
    
    if [ -n "$NPM_PROCS" ]; then
        echo "✅ Frontend processes: $NPM_PROCS"
    else
        echo "❌ No frontend processes found"
    fi
else
    echo "⚠️ pgrep not available, cannot check processes"
fi

# Check PID files
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "✅ Backend PID file valid: $BACKEND_PID (running)"
    else
        echo "❌ Backend PID file exists but process not running: $BACKEND_PID"
    fi
fi

if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "✅ Frontend PID file valid: $FRONTEND_PID (running)"
    else
        echo "❌ Frontend PID file exists but process not running: $FRONTEND_PID"
    fi
fi

echo ""
echo "📝 Log Analysis:"
if [ -f logs/backend.log ]; then
    BACKEND_SIZE=$(wc -l < logs/backend.log)
    echo "Backend log: $BACKEND_SIZE lines"
    
    # Check for recent errors
    RECENT_ERRORS=$(tail -100 logs/backend.log | grep -i "error\|exception\|failed" | wc -l)
    if [ $RECENT_ERRORS -gt 0 ]; then
        echo "⚠️ Recent errors in backend log: $RECENT_ERRORS"
        echo "Last few errors:"
        tail -100 logs/backend.log | grep -i "error\|exception\|failed" | tail -3 | sed 's/^/  /'
    else
        echo "✅ No recent errors in backend log"
    fi
    
    # Check for startup messages
    if grep -q "Started server" logs/backend.log; then
        echo "✅ Backend startup detected in logs"
    else
        echo "❌ No backend startup message found"
    fi
else
    echo "❌ Backend log not found"
fi

if [ -f logs/frontend.log ]; then
    FRONTEND_SIZE=$(wc -l < logs/frontend.log)
    echo "Frontend log: $FRONTEND_SIZE lines"
    
    # Check for compilation/build success
    if grep -q -i "compiled\|built\|ready" logs/frontend.log; then
        echo "✅ Frontend build/compilation detected"
    else
        echo "❌ No frontend build success message found"
    fi
    
    # Check for errors
    FRONTEND_ERRORS=$(tail -50 logs/frontend.log | grep -i "error\|failed" | wc -l)
    if [ $FRONTEND_ERRORS -gt 0 ]; then
        echo "⚠️ Recent errors in frontend log: $FRONTEND_ERRORS"
    else
        echo "✅ No recent errors in frontend log"
    fi
else
    echo "❌ Frontend log not found"
fi

echo ""
echo "🌐 Network Connectivity:"
# Test local endpoints
if curl -f http://localhost:3000/api/options >/dev/null 2>&1; then
    echo "✅ Backend API responding (http://localhost:3000)"
else
    echo "❌ Backend API not responding"
fi

if curl -f http://localhost:3001 >/dev/null 2>&1; then
    echo "✅ Frontend responding (http://localhost:3001)"
else
    echo "❌ Frontend not responding"
fi

# Test external connectivity
if curl -f https://api.deepseek.com >/dev/null 2>&1; then
    echo "✅ DeepSeek API reachable"
else
    echo "⚠️ DeepSeek API not reachable (may be normal without API key)"
fi

echo ""
echo "💾 Resource Usage:"
if command -v free >/dev/null 2>&1; then
    echo "Memory usage:"
    free -h | sed 's/^/  /'
    
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$MEM_USAGE > 80" | bc -l 2>/dev/null || echo "0") )); then
        echo "⚠️ High memory usage: ${MEM_USAGE}%"
    fi
fi

if command -v df >/dev/null 2>&1; then
    echo "Disk usage (relevant mounts):"
    df -h / /tmp 2>/dev/null | sed 's/^/  /' || df -h | head -2 | sed 's/^/  /'
fi

echo ""
echo "🔍 Integration File Check:"
INTEGRATION_FILES=(
    "openhands/llm/deepseek_r1.py"
    "openhands/llm/enhanced_llm.py"
    "openhands/llm/fallback_manager.py"
    "tests/unit/test_deepseek_r1.py"
    "tests/unit/test_enhanced_llm.py"
    "tests/unit/test_fallback_manager.py"
)

for file in "${INTEGRATION_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

echo ""
echo "🎯 Recommendations:"

# Check for common issues and provide recommendations
if ! command -v node >/dev/null 2>&1; then
    echo "⚠️ Install Node.js: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "⚠️ Install Python 3: sudo apt-get update && sudo apt-get install -y python3 python3-pip"
fi

if [ ! -f .env ]; then
    echo "⚠️ Create .env file: cp .env.example .env (or run ./startup.sh)"
fi

if [ ! -d /tmp/openhands_workspace ]; then
    echo "⚠️ Create workspace directory: mkdir -p /tmp/openhands_workspace"
fi

if [ ! -d logs ]; then
    echo "⚠️ Create logs directory: mkdir -p logs"
fi

if [ ! -f config.toml ]; then
    echo "⚠️ Create configuration file (run ./startup.sh to generate)"
fi

# Check if services are not running
if ! pgrep -f "openhands.server.listen" >/dev/null 2>&1; then
    echo "⚠️ Start backend service: ./startup.sh"
fi

if ! pgrep -f "npm run start" >/dev/null 2>&1; then
    echo "⚠️ Frontend may not be running (check with ./startup.sh)"
fi

echo ""
echo "🚀 Quick Actions:"
echo "- Start services: ./startup.sh"
echo "- Test integration: ./test_integration.sh"
echo "- View backend logs: tail -f logs/backend.log"
echo "- View frontend logs: tail -f logs/frontend.log"
echo "- Stop services: pkill -f 'openhands.server.listen' && pkill -f 'npm run start'"
echo "- Check processes: ps aux | grep -E 'openhands|npm'"

echo ""
echo "✅ Diagnostic complete!"
echo "If you're experiencing issues, check the recommendations above and review the log files."