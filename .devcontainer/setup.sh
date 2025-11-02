#!/bin/bash

# Mark the current repository as safe for Git to prevent "dubious ownership" errors,
# which can occur in containerized environments when directory ownership doesn't match the current user.
git config --global --add safe.directory "$(realpath .)"

# Install `nc`
sudo apt update && sudo apt install netcat -y

# Install uv (which includes uvx)
if ! command -v uv &> /dev/null; then
    echo "Installing uv (which includes uvx)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    # Also add to PATH for future sessions
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
fi

# Do common setup tasks
source .openhands/setup.sh
