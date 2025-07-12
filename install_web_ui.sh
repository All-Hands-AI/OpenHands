#!/bin/bash

# OpenHands Termux Web UI Installer
# Installs web interface untuk OpenHands Termux

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="$HOME/openhands_web_ui_install.log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Header
print_header() {
    clear
    log "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${PURPLE}║                                                              ║${NC}"
    log "${PURPLE}║              🚀 OpenHands Termux Web UI Installer           ║${NC}"
    log "${PURPLE}║                                                              ║${NC}"
    log "${PURPLE}║              Modern Web Interface for OpenHands              ║${NC}"
    log "${PURPLE}║                                                              ║${NC}"
    log "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
}

# Check if running in Termux
check_termux() {
    if [[ ! -d "/data/data/com.termux" ]]; then
        log_error "This installer is designed for Termux on Android"
        log_error "Please run this script in Termux environment"
        exit 1
    fi
    log_success "Running in Termux environment"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_deps+=("nodejs")
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        missing_deps+=("nodejs") # npm comes with nodejs
    fi
    
    # Check Python
    if ! command -v python &> /dev/null; then
        missing_deps+=("python")
    fi
    
    # Check pip
    if ! command -v pip &> /dev/null; then
        missing_deps+=("python-pip")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_warning "Missing dependencies: ${missing_deps[*]}"
        log_info "Installing missing dependencies..."
        
        pkg update -y
        for dep in "${missing_deps[@]}"; do
            log_info "Installing $dep..."
            pkg install -y "$dep"
        done
    fi
    
    log_success "All dependencies are available"
}

# Install Python dependencies
install_python_deps() {
    log_info "Installing Python dependencies for web server..."
    
    pip install --upgrade pip
    pip install fastapi uvicorn websockets psutil
    
    # Optional dependencies
    log_info "Installing optional dependencies..."
    pip install litellm || log_warning "LiteLLM installation failed (optional)"
    
    log_success "Python dependencies installed"
}

# Install Node.js dependencies and build
install_and_build_ui() {
    log_info "Installing Node.js dependencies and building web UI..."
    
    cd termux_web_ui
    
    # Install dependencies
    log_info "Installing npm packages..."
    npm install
    
    # Build for production
    log_info "Building web UI for production..."
    npm run build
    
    cd ..
    log_success "Web UI built successfully"
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Web UI server script
    cat > start_web_ui.sh << 'EOF'
#!/bin/bash

# OpenHands Termux Web UI Startup Script

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting OpenHands Termux Web UI...${NC}"

# Check if server is already running
if pgrep -f "termux_web_ui_server.py" > /dev/null; then
    echo -e "${YELLOW}⚠️ Web UI server is already running${NC}"
    echo -e "${BLUE}📱 Access at: http://localhost:8000${NC}"
    exit 0
fi

# Start the server
echo -e "${BLUE}📡 Starting web server on port 8000...${NC}"
python termux_web_ui_server.py --host 0.0.0.0 --port 8000 &

# Wait a moment for server to start
sleep 3

# Check if server started successfully
if pgrep -f "termux_web_ui_server.py" > /dev/null; then
    echo -e "${GREEN}✅ Web UI server started successfully!${NC}"
    echo -e "${BLUE}📱 Access at: http://localhost:8000${NC}"
    echo -e "${BLUE}🌐 Or from other devices: http://$(hostname -I | awk '{print $1}'):8000${NC}"
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo -e "   • Configure your API key in Settings"
    echo -e "   • Use the Terminal tab for command execution"
    echo -e "   • Monitor system resources in the Monitor tab"
    echo -e "   • Press Ctrl+C to stop the server"
    echo ""
else
    echo -e "${RED}❌ Failed to start web UI server${NC}"
    exit 1
fi

# Keep script running
wait
EOF

    chmod +x start_web_ui.sh
    
    # Stop script
    cat > stop_web_ui.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping OpenHands Termux Web UI..."

# Kill the server process
pkill -f "termux_web_ui_server.py"

if ! pgrep -f "termux_web_ui_server.py" > /dev/null; then
    echo "✅ Web UI server stopped successfully"
else
    echo "❌ Failed to stop web UI server"
    exit 1
fi
EOF

    chmod +x stop_web_ui.sh
    
    log_success "Startup scripts created"
}

# Create desktop shortcut (if supported)
create_shortcuts() {
    log_info "Creating shortcuts..."
    
    # Create .desktop file for app launcher
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$HOME/.local/share/applications/openhands-termux.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=OpenHands Termux
Comment=AI Assistant for Android
Exec=termux-open-url http://localhost:8000
Icon=web-browser
Terminal=false
Categories=Development;Utility;
EOF
    
    log_success "Shortcuts created"
}

# Setup auto-start (optional)
setup_autostart() {
    log_info "Setting up auto-start configuration..."
    
    # Create termux boot script directory
    mkdir -p "$HOME/.termux/boot"
    
    cat > "$HOME/.termux/boot/start-openhands-web" << 'EOF'
#!/bin/bash

# Auto-start OpenHands Web UI on Termux boot
# Remove this file to disable auto-start

sleep 10  # Wait for system to be ready

cd "$HOME/OpenHands" || exit 1

# Start web UI in background
nohup ./start_web_ui.sh > /dev/null 2>&1 &

# Send notification
termux-notification --title "OpenHands" --content "Web UI started automatically" || true
EOF

    chmod +x "$HOME/.termux/boot/start-openhands-web"
    
    log_success "Auto-start configured (will start on next Termux boot)"
}

# Create configuration
create_config() {
    log_info "Creating default configuration..."
    
    cat > web_ui_config.json << 'EOF'
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "auto_start": false
  },
  "ui": {
    "theme": "dark",
    "auto_refresh_interval": 5000,
    "max_chat_history": 100
  },
  "features": {
    "terminal": true,
    "system_monitor": true,
    "file_manager": true,
    "chat_streaming": true
  }
}
EOF
    
    log_success "Configuration created"
}

# Main installation
main() {
    print_header
    
    log_info "Starting OpenHands Termux Web UI installation..."
    log_info "Installation log: $LOG_FILE"
    
    # Pre-installation checks
    check_termux
    check_dependencies
    
    # Installation steps
    install_python_deps
    install_and_build_ui
    create_startup_scripts
    create_shortcuts
    create_config
    
    # Optional features
    read -p "$(echo -e ${YELLOW}Do you want to enable auto-start on boot? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_autostart
    fi
    
    # Installation complete
    log ""
    log_success "🎉 OpenHands Termux Web UI installation completed!"
    log ""
    log "${CYAN}📋 Quick Start:${NC}"
    log "   1. Start the web UI: ${GREEN}./start_web_ui.sh${NC}"
    log "   2. Open browser: ${GREEN}http://localhost:8000${NC}"
    log "   3. Configure API key in Settings"
    log "   4. Start chatting with AI!"
    log ""
    log "${CYAN}📁 Files created:${NC}"
    log "   • ${GREEN}start_web_ui.sh${NC} - Start the web server"
    log "   • ${GREEN}stop_web_ui.sh${NC} - Stop the web server"
    log "   • ${GREEN}web_ui_config.json${NC} - Configuration file"
    log "   • ${GREEN}termux_web_ui/${NC} - Web UI source code"
    log ""
    log "${CYAN}🔧 Management:${NC}"
    log "   • Start: ${GREEN}./start_web_ui.sh${NC}"
    log "   • Stop: ${GREEN}./stop_web_ui.sh${NC}"
    log "   • Logs: ${GREEN}tail -f $LOG_FILE${NC}"
    log ""
    
    # Ask to start now
    read -p "$(echo -e ${YELLOW}Do you want to start the web UI now? [Y/n]: ${NC})" -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        log_info "Starting web UI..."
        ./start_web_ui.sh
    fi
}

# Run main function
main "$@"