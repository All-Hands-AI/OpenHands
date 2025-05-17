#! /bin/bash

echo "Setting up the environment..."

# Install pre-commit package
python -m pip install pre-commit

# Install pre-commit hooks if .git directory exists
if [ -d ".git" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi
