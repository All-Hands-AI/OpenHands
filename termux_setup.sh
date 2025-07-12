#!/data/data/com.termux/files/usr/bin/bash

# OpenHands Termux Setup Script
# Script untuk menginstall OpenHands di Termux

set -e

echo "🚀 OpenHands Termux Setup"
echo "========================="

# Update packages
echo "📦 Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Install required packages
echo "📦 Installing required packages..."
pkg install -y python python-pip git nodejs npm rust binutils clang make cmake pkg-config libffi openssl zlib libjpeg-turbo

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install minimal dependencies for Termux
echo "📦 Installing OpenHands dependencies..."
pip install litellm aiohttp fastapi uvicorn python-dotenv toml termcolor jinja2 tenacity pyjwt requests prompt-toolkit

# Create directories
echo "📁 Creating directories..."
mkdir -p ~/.openhands
mkdir -p ~/.openhands/workspace
mkdir -p ~/.openhands/config

# Copy configuration files
echo "⚙️ Setting up configuration..."
cp termux_config.toml ~/.openhands/config/config.toml

# Make CLI executable
echo "🔧 Setting up CLI..."
chmod +x termux_cli.py
ln -sf $(pwd)/termux_cli.py ~/.openhands/openhands

# Add to PATH
echo "🔗 Adding to PATH..."
echo 'export PATH="$HOME/.openhands:$PATH"' >> ~/.bashrc

echo ""
echo "✅ OpenHands Termux setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Termux or run: source ~/.bashrc"
echo "2. Configure your API key: openhands config"
echo "3. Start using: openhands chat"
echo ""
echo "📖 For help: openhands --help"