#!/data/data/com.termux/files/usr/bin/bash

# OpenHands Termux All-in-One Installer v2.0
# Installer lengkap untuk OpenHands di Termux (No Root Required)
# Mendukung CLI, Web UI, Git Integration, dan semua fitur
# Compatible dengan Termux dan Proot environment

set -e

# Colors untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji untuk visual feedback
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
INFO="ℹ️"
GEAR="⚙️"
PACKAGE="📦"
PYTHON="🐍"
FOLDER="📁"
LINK="🔗"
SAVE="💾"
FIRE="🔥"

# Global variables
INSTALL_DIR="$HOME/.openhands"
BACKUP_DIR="$HOME/.openhands_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$HOME/openhands_install.log"
PYTHON_VERSION=""
TERMUX_VERSION=""
ANDROID_VERSION=""

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Error handling
error_exit() {
    log "${CROSS} ERROR: $1"
    echo -e "${RED}${CROSS} Installation failed. Check log: $LOG_FILE${NC}"
    exit 1
}

# Success message
success() {
    log "${CHECK} $1"
}

# Warning message
warning() {
    log "${WARNING} $1"
}

# Info message
info() {
    log "${INFO} $1"
}

# Check if running in Termux
check_termux() {
    info "Checking Termux environment..."
    
    if [[ ! -d "/data/data/com.termux" ]]; then
        error_exit "This installer is designed for Termux only!"
    fi
    
    # Check if we have proper Termux environment
    if [[ ! -f "$PREFIX/bin/pkg" ]]; then
        error_exit "Termux package manager not found!"
    fi
    
    success "Running in Termux environment"
    
    # Get Termux version
    if command -v termux-info >/dev/null 2>&1; then
        TERMUX_VERSION=$(termux-info | grep "Termux version" | cut -d: -f2 | xargs)
        info "Termux version: $TERMUX_VERSION"
    fi
    
    # Get Android version
    if [[ -f "/system/build.prop" ]]; then
        ANDROID_VERSION=$(getprop ro.build.version.release 2>/dev/null || echo "Unknown")
        info "Android version: $ANDROID_VERSION"
    fi
}

# Check system requirements
check_requirements() {
    info "Checking system requirements..."
    
    # Check available space (minimum 2GB)
    available_space=$(df "$HOME" | awk 'NR==2 {print $4}')
    required_space=2097152  # 2GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        error_exit "Insufficient storage space. Need at least 2GB free space."
    fi
    
    success "Storage space check passed"
    
    # Check internet connection
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        error_exit "No internet connection. Please check your network."
    fi
    
    success "Internet connection check passed"
    
    # Check architecture
    ARCH=$(uname -m)
    info "System architecture: $ARCH"
    
    case $ARCH in
        aarch64|arm64)
            success "ARM64 architecture supported"
            ;;
        armv7l|armv8l)
            success "ARM architecture supported"
            ;;
        x86_64)
            success "x86_64 architecture supported"
            ;;
        *)
            warning "Unsupported architecture: $ARCH. Installation may fail."
            ;;
    esac
}

# Backup existing installation
backup_existing() {
    if [[ -d "$INSTALL_DIR" ]]; then
        info "Backing up existing installation..."
        cp -r "$INSTALL_DIR" "$BACKUP_DIR"
        success "Backup created at: $BACKUP_DIR"
    fi
}

# Update Termux packages
update_termux() {
    info "Updating Termux packages..."
    
    # Update package lists
    pkg update -y || error_exit "Failed to update package lists"
    
    # Upgrade existing packages
    pkg upgrade -y || error_exit "Failed to upgrade packages"
    
    success "Termux packages updated"
}

# Install system dependencies
install_system_deps() {
    info "Installing system dependencies..."
    
    local packages=(
        "python"
        "python-pip"
        "git"
        "nodejs"
        "npm"
        "rust"
        "binutils"
        "clang"
        "make"
        "cmake"
        "pkg-config"
        "libffi"
        "openssl"
        "zlib"
        "libjpeg-turbo"
        "libpng"
        "freetype"
        "curl"
        "wget"
        "unzip"
        "tar"
        "gzip"
        "which"
        "tree"
        "htop"
        "nano"
        "vim"
    )
    
    for package in "${packages[@]}"; do
        info "Installing $package..."
        if pkg install -y "$package"; then
            success "$package installed"
        else
            warning "Failed to install $package, continuing..."
        fi
    done
    
    # Get Python version
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    info "Python version: $PYTHON_VERSION"
    
    success "System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    info "Installing Python dependencies..."
    
    # Upgrade pip first
    python -m pip install --upgrade pip setuptools wheel || error_exit "Failed to upgrade pip"
    
    # Core dependencies
    local core_deps=(
        "litellm>=1.60.0"
        "aiohttp>=3.9.0"
        "fastapi"
        "uvicorn[standard]"
        "toml"
        "python-dotenv"
        "termcolor"
        "jinja2>=3.1.3"
        "tenacity>=8.5"
        "pyjwt>=2.9.0"
        "requests"
        "prompt-toolkit>=3.0.50"
        "json-repair"
        "pathspec>=0.12.1"
        "whatthepatch>=1.0.6"
        "psutil"
    )
    
    # Optional dependencies for enhanced features
    local optional_deps=(
        "numpy"
        "pandas"
        "matplotlib"
        "seaborn"
        "beautifulsoup4"
        "lxml"
        "Pillow"
    )
    
    # Install core dependencies
    for dep in "${core_deps[@]}"; do
        info "Installing $dep..."
        if python -m pip install "$dep"; then
            success "$dep installed"
        else
            error_exit "Failed to install critical dependency: $dep"
        fi
    done
    
    # Install optional dependencies (non-critical)
    for dep in "${optional_deps[@]}"; do
        info "Installing optional dependency: $dep..."
        if python -m pip install "$dep"; then
            success "$dep installed"
        else
            warning "Failed to install optional dependency: $dep"
        fi
    done
    
    success "Python dependencies installed"
}

# Setup directories
setup_directories() {
    info "Setting up directories..."
    
    local dirs=(
        "$INSTALL_DIR"
        "$INSTALL_DIR/config"
        "$INSTALL_DIR/workspace"
        "$INSTALL_DIR/cache"
        "$INSTALL_DIR/trajectories"
        "$INSTALL_DIR/file_store"
        "$INSTALL_DIR/logs"
        "$INSTALL_DIR/backups"
        "$INSTALL_DIR/examples"
        "$INSTALL_DIR/scripts"
    )
    
    for dir in "${dirs[@]}"; do
        if mkdir -p "$dir"; then
            success "Created directory: $dir"
        else
            error_exit "Failed to create directory: $dir"
        fi
    done
    
    success "Directories setup completed"
}

# Install OpenHands files
install_openhands_files() {
    info "Installing OpenHands files..."
    
    # Copy main files
    local files=(
        "termux_cli.py:openhands"
        "termux_agent.py:termux_agent.py"
        "termux_config.toml:config/config.toml"
        "requirements-termux.txt:requirements.txt"
        "examples_termux.md:examples/examples.md"
        "README_TERMUX.md:README.md"
        "INSTALL_TERMUX.md:INSTALL.md"
    )
    
    for file_mapping in "${files[@]}"; do
        local src="${file_mapping%:*}"
        local dst="$INSTALL_DIR/${file_mapping#*:}"
        
        if [[ -f "$src" ]]; then
            if cp "$src" "$dst"; then
                success "Copied $src to $dst"
            else
                error_exit "Failed to copy $src"
            fi
        else
            warning "Source file not found: $src"
        fi
    done
    
    # Make CLI executable
    chmod +x "$INSTALL_DIR/openhands" || error_exit "Failed to make CLI executable"
    
    success "OpenHands files installed"
}

# Setup CLI and PATH
setup_cli() {
    info "Setting up CLI and PATH..."
    
    # Add to PATH in .bashrc
    local bashrc="$HOME/.bashrc"
    local path_line='export PATH="$HOME/.openhands:$PATH"'
    
    if [[ -f "$bashrc" ]]; then
        if ! grep -q "$path_line" "$bashrc"; then
            echo "" >> "$bashrc"
            echo "# OpenHands Termux" >> "$bashrc"
            echo "$path_line" >> "$bashrc"
            success "Added OpenHands to PATH in .bashrc"
        else
            info "OpenHands already in PATH"
        fi
    else
        echo "$path_line" > "$bashrc"
        success "Created .bashrc with OpenHands PATH"
    fi
    
    # Create convenient aliases
    local aliases=(
        'alias oh="openhands"'
        'alias ohchat="openhands chat"'
        'alias ohconfig="openhands config"'
        'alias ohhelp="openhands --help"'
    )
    
    for alias_line in "${aliases[@]}"; do
        if ! grep -q "$alias_line" "$bashrc"; then
            echo "$alias_line" >> "$bashrc"
        fi
    done
    
    success "CLI setup completed"
}

# Install additional tools and scripts
install_additional_tools() {
    info "Installing additional tools..."
    
    # Create system monitor script
    if [[ -f "system_monitor.py" ]]; then
        cp "system_monitor.py" "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/system_monitor.py"
        success "System monitor installed"
    fi
    
    # Create backup script
    if [[ -f "backup_termux.py" ]]; then
        cp "backup_termux.py" "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/backup_termux.py"
        success "Backup tool installed"
    fi
    
    # Create weather checker
    if [[ -f "weather_checker.py" ]]; then
        cp "weather_checker.py" "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/weather_checker.py"
        success "Weather checker installed"
    fi
    
    # Create data analyzer
    if [[ -f "data_analyzer.py" ]]; then
        cp "data_analyzer.py" "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/data_analyzer.py"
        success "Data analyzer installed"
    fi
    
    success "Additional tools installed"
}

# Install Node.js and Web UI dependencies
install_web_ui() {
    info "Installing Web UI components..."
    
    # Install Node.js if not present
    if ! command -v node >/dev/null 2>&1; then
        info "Installing Node.js..."
        pkg install -y nodejs npm || error_exit "Failed to install Node.js"
        success "Node.js installed"
    else
        info "Node.js already installed: $(node --version)"
    fi
    
    # Check if web UI directory exists
    if [[ -d "termux_web_ui" ]]; then
        info "Installing Web UI dependencies..."
        cd termux_web_ui
        
        # Install npm dependencies
        npm install || error_exit "Failed to install npm dependencies"
        
        # Build production version
        npm run build || warning "Failed to build production version (development mode will be used)"
        
        cd ..
        success "Web UI dependencies installed"
    else
        warning "Web UI directory not found, skipping web UI installation"
    fi
    
    # Copy web UI server
    if [[ -f "termux_web_ui_server.py" ]]; then
        cp "termux_web_ui_server.py" "$INSTALL_DIR/"
        chmod +x "$INSTALL_DIR/termux_web_ui_server.py"
        success "Web UI server installed"
    fi
    
    # Copy web UI scripts
    local web_scripts=(
        "install_web_ui.sh"
        "start_web_ui.sh"
        "stop_web_ui.sh"
        "test_web_ui.sh"
    )
    
    for script in "${web_scripts[@]}"; do
        if [[ -f "$script" ]]; then
            cp "$script" "$INSTALL_DIR/"
            chmod +x "$INSTALL_DIR/$script"
            info "Copied $script"
        fi
    done
    
    # Copy web UI directory
    if [[ -d "termux_web_ui" ]]; then
        cp -r "termux_web_ui" "$INSTALL_DIR/"
        success "Web UI files copied"
    fi
    
    success "Web UI installation completed"
}

# Setup Termux API integration
setup_termux_api() {
    info "Setting up Termux API integration..."
    
    # Install Termux:API if not present
    if ! command -v termux-battery-status >/dev/null 2>&1; then
        warning "Termux:API not found. Install from F-Droid for enhanced features."
        info "Download: https://f-droid.org/packages/com.termux.api/"
    else
        success "Termux:API detected"
        
        # Test API functionality
        if termux-battery-status >/dev/null 2>&1; then
            success "Termux:API working correctly"
        else
            warning "Termux:API installed but not working properly"
        fi
    fi
}

# Create desktop shortcuts (if supported)
create_shortcuts() {
    info "Creating shortcuts..."
    
    # Create bin directory shortcuts
    local bin_dir="$HOME/bin"
    mkdir -p "$bin_dir"
    
    # Create symlinks for easy access
    local shortcuts=(
        "openhands:$INSTALL_DIR/openhands"
        "oh:$INSTALL_DIR/openhands"
        "system-monitor:$INSTALL_DIR/scripts/system_monitor.py"
        "backup-termux:$INSTALL_DIR/scripts/backup_termux.py"
        "weather:$INSTALL_DIR/scripts/weather_checker.py"
        "analyze-data:$INSTALL_DIR/scripts/data_analyzer.py"
    )
    
    for shortcut in "${shortcuts[@]}"; do
        local name="${shortcut%:*}"
        local target="${shortcut#*:}"
        
        if [[ -f "$target" ]]; then
            ln -sf "$target" "$bin_dir/$name"
            success "Created shortcut: $name"
        fi
    done
}

# Run tests
run_tests() {
    info "Running installation tests..."
    
    if [[ -f "test_termux.py" ]]; then
        if python test_termux.py; then
            success "All tests passed"
        else
            warning "Some tests failed, but installation may still work"
        fi
    else
        warning "Test script not found, skipping tests"
    fi
}

# Setup storage access
setup_storage() {
    info "Setting up storage access..."
    
    if command -v termux-setup-storage >/dev/null 2>&1; then
        info "Run 'termux-setup-storage' to access Android storage"
        info "This will allow OpenHands to access /sdcard"
    else
        warning "termux-setup-storage not available"
    fi
}

# Create welcome message
create_welcome() {
    local welcome_file="$INSTALL_DIR/WELCOME.md"
    
    cat > "$welcome_file" << 'EOF'
# 🎉 Welcome to OpenHands Termux v2.0!

OpenHands has been successfully installed on your Termux environment with full Web UI support!

## 🚀 Quick Start

### 🌐 Web UI (Recommended)
1. **Start Web UI:**
   ```bash
   cd ~/.openhands
   ./start_web_ui.sh
   ```

2. **Access in Browser:**
   - Local: http://localhost:8000
   - Mobile: http://YOUR_IP:8000

3. **Install as PWA:**
   - Open in Chrome/Firefox
   - Menu → "Add to Home Screen"

### 💻 Command Line
1. **Configure API Key:**
   ```bash
   openhands config
   ```

2. **Start Chatting:**
   ```bash
   openhands chat
   ```

3. **Get Help:**
   ```bash
   openhands --help
   ```

## 🛠️ Available Tools

### Web Interface
- `start_web_ui.sh` - Start web interface
- `stop_web_ui.sh` - Stop web interface
- `test_web_ui.sh` - Test web UI installation

### Command Line Tools
- `openhands` or `oh` - Main CLI
- `system-monitor` - System monitoring
- `backup-termux` - Backup tool
- `weather` - Weather checker
- `analyze-data` - Data analysis

## ✨ Features

### 🌐 Web UI Features
- 🤖 AI Chat with streaming responses
- 📁 File browser with visual management
- 🔧 Git integration with GitHub support
- 💻 Built-in terminal
- 📊 Real-time system monitoring
- 📱 Mobile-optimized interface
- 📴 Progressive Web App support

### 🔧 Default Configuration
- **API Provider**: LLM7 (free, no API key required)
- **Base URL**: https://api.llm7.io/v1
- **Model**: gpt-3.5-turbo
- **Web Port**: 8000

## 📚 Documentation

- Web UI Guide: `~/.openhands/README_WEB_UI.md`
- Main README: `~/.openhands/README_TERMUX.md`
- Installation Guide: `~/.openhands/INSTALL_TERMUX.md`
- Examples: `~/.openhands/examples_termux.md`
- Changelog: `~/.openhands/CHANGELOG_TERMUX.md`

## 🆘 Support

- Check logs: `~/openhands_install.log`
- Run tests: `python ~/.openhands/test_termux.py`
- Web UI tests: `~/.openhands/test_web_ui.sh`
- GitHub Issues: https://github.com/mulkymalikuldhrs/OpenHands/issues

## 🎯 Next Steps

1. **Start Web UI**: `cd ~/.openhands && ./start_web_ui.sh`
2. **Open Browser**: http://localhost:8000
3. **Install as PWA**: Add to Home Screen
4. **Explore Features**: Chat, Files, Git, Terminal, Monitor
5. **Configure Settings**: API keys, models, preferences
6. **Join Community**: Share feedback and contribute!

## 🔧 Troubleshooting

- **Port in use**: `./stop_web_ui.sh`
- **Node.js issues**: `pkg install nodejs npm`
- **Build errors**: `cd termux_web_ui && npm install`
- **Permission issues**: `termux-setup-storage`

Happy coding with OpenHands Termux v2.0! 🚀📱
EOF

    success "Welcome guide created"
}

# Main installation function
main_install() {
    echo -e "${BLUE}"
    cat << 'EOF'
   ____                   _   _                 _     
  / __ \                 | | | |               | |    
 | |  | |_ __   ___ _ __ | |_| | __ _ _ __   __| |___ 
 | |  | | '_ \ / _ \ '_ \|  _  |/ _` | '_ \ / _` / __|
 | |__| | |_) |  __/ | | | | | | (_| | | | | (_| \__ \
  \____/| .__/ \___|_| |_\_| |_/\__,_|_| |_|\__,_|___/
        | |                                          
        |_|                                          
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}${ROCKET} OpenHands Termux All-in-One Installer${NC}"
    echo -e "${CYAN}==========================================${NC}"
    echo ""
    echo -e "${YELLOW}This installer will set up OpenHands on your Termux environment.${NC}"
    echo -e "${YELLOW}The installation includes:${NC}"
    echo -e "${YELLOW}- Core OpenHands with custom API support${NC}"
    echo -e "${YELLOW}- System monitoring tools${NC}"
    echo -e "${YELLOW}- Backup and restore utilities${NC}"
    echo -e "${YELLOW}- Weather checker${NC}"
    echo -e "${YELLOW}- Data analysis tools${NC}"
    echo -e "${YELLOW}- And much more!${NC}"
    echo ""
    
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled.${NC}"
        exit 0
    fi
    
    echo -e "${GREEN}${ROCKET} Starting installation...${NC}"
    echo ""
    
    # Start logging
    echo "OpenHands Termux Installation Log" > "$LOG_FILE"
    echo "Started at: $(date)" >> "$LOG_FILE"
    echo "===============================" >> "$LOG_FILE"
    
    # Installation steps
    local steps=(
        "check_termux:Checking Termux environment"
        "check_requirements:Checking system requirements"
        "backup_existing:Backing up existing installation"
        "update_termux:Updating Termux packages"
        "install_system_deps:Installing system dependencies"
        "install_python_deps:Installing Python dependencies"
        "setup_directories:Setting up directories"
        "install_openhands_files:Installing OpenHands files"
        "setup_cli:Setting up CLI and PATH"
        "install_additional_tools:Installing additional tools"
        "install_web_ui:Installing Web UI components"
        "setup_termux_api:Setting up Termux API integration"
        "create_shortcuts:Creating shortcuts"
        "setup_storage:Setting up storage access"
        "create_welcome:Creating welcome guide"
        "run_tests:Running tests"
    )
    
    local total_steps=${#steps[@]}
    local current_step=0
    
    for step in "${steps[@]}"; do
        local func="${step%:*}"
        local desc="${step#*:}"
        
        current_step=$((current_step + 1))
        echo -e "${BLUE}[${current_step}/${total_steps}] ${desc}...${NC}"
        
        if $func; then
            echo -e "${GREEN}${CHECK} Step ${current_step} completed${NC}"
        else
            echo -e "${RED}${CROSS} Step ${current_step} failed${NC}"
            error_exit "Installation failed at step: $desc"
        fi
        
        echo ""
    done
    
    # Installation completed
    echo -e "${GREEN}${FIRE} Installation completed successfully!${NC}"
    echo ""
    echo -e "${CYAN}${INFO} Installation Summary:${NC}"
    echo -e "  ${CHECK} OpenHands v2.0 installed to: ${INSTALL_DIR}"
    echo -e "  ${CHECK} CLI available as: openhands, oh"
    echo -e "  ${CHECK} Web UI available on port 8000"
    echo -e "  ${CHECK} Python version: ${PYTHON_VERSION}"
    echo -e "  ${CHECK} Node.js version: $(node --version 2>/dev/null || echo 'Not installed')"
    echo -e "  ${CHECK} Termux version: ${TERMUX_VERSION}"
    echo -e "  ${CHECK} Android version: ${ANDROID_VERSION}"
    echo -e "  ${CHECK} Log file: ${LOG_FILE}"
    if [[ -d "$BACKUP_DIR" ]]; then
        echo -e "  ${CHECK} Backup created: ${BACKUP_DIR}"
    fi
    echo ""
    echo -e "${YELLOW}${ROCKET} Quick Start:${NC}"
    echo -e "  ${CYAN}🌐 Web UI (Recommended):${NC}"
    echo -e "    cd ~/.openhands && ./start_web_ui.sh"
    echo -e "    Open: http://localhost:8000"
    echo ""
    echo -e "  ${CYAN}💻 Command Line:${NC}"
    echo -e "    openhands config  # Configure API"
    echo -e "    openhands chat    # Start chatting"
    echo ""
    echo -e "${YELLOW}${INFO} Features Available:${NC}"
    echo -e "  ${CHECK} AI Chat with LLM7 (free API)"
    echo -e "  ${CHECK} File browser and management"
    echo -e "  ${CHECK} Git integration with GitHub"
    echo -e "  ${CHECK} Built-in terminal"
    echo -e "  ${CHECK} System monitoring"
    echo -e "  ${CHECK} Progressive Web App"
    echo -e "  ${CHECK} Mobile-optimized interface"
    echo ""
    echo -e "${YELLOW}${ROCKET} Next Steps:${NC}"
    echo -e "  1. Start Web UI: ${CYAN}cd ~/.openhands && ./start_web_ui.sh${NC}"
    echo -e "  2. Open browser: ${CYAN}http://localhost:8000${NC}"
    echo -e "  3. Install as PWA: Add to Home Screen"
    echo -e "  4. Read guide: ${CYAN}cat ~/.openhands/WELCOME.md${NC}"
    echo ""
    echo -e "${GREEN}${ROCKET} Happy coding with OpenHands Termux v2.0! ${ROCKET}${NC}"
}

# Cleanup function
cleanup() {
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}${CROSS} Installation failed!${NC}"
        echo -e "${YELLOW}${INFO} Check the log file: $LOG_FILE${NC}"
        
        if [[ -d "$BACKUP_DIR" ]]; then
            echo -e "${YELLOW}${INFO} Backup available at: $BACKUP_DIR${NC}"
        fi
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Run main installation
main_install