#!/bin/bash
#
# Shell script wrapper for building OpenHands CLI executable.
#
# This script provides a simple interface to build the OpenHands CLI
# using PyInstaller with uv package management.
#

set -e  # Exit on any error

echo "🚀 OpenHands CLI Build Script"
echo "=============================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required but not found! Please install uv first."
    exit 1
fi

# Parse arguments to check for --install-pyinstaller
INSTALL_PYINSTALLER=false
PYTHON_ARGS=()

for arg in "$@"; do
    case $arg in
        --install-pyinstaller)
            INSTALL_PYINSTALLER=true
            PYTHON_ARGS+=("$arg")
            ;;
        *)
            PYTHON_ARGS+=("$arg")
            ;;
    esac
done

# Install PyInstaller if requested
if [ "$INSTALL_PYINSTALLER" = true ]; then
    echo "📦 Installing PyInstaller with uv..."
    if uv add --dev pyinstaller; then
        echo "✅ PyInstaller installed successfully with uv!"
    else
        echo "❌ Failed to install PyInstaller"
        exit 1
    fi
fi

# Run the Python build script using uv
uv run python build.py "${PYTHON_ARGS[@]}"
