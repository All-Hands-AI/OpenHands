#!/usr/bin/env bash
sudo apt update
sudo apt install -y netcat
sudo add-apt-repository -y ppa:deadsnakes/ppa
curl -sSL https://install.python-poetry.org | python3.12 -

# See: https://github.com/SmartManoj/Kevin/issues/122#issuecomment-2540482254
git config --global --add safe.directory /workspaces/OpenHands

# Global .gitignore for VS Code
echo ".history/" > ~/.gitignore_global
git config --global core.excludesfile ~/.gitignore_global
