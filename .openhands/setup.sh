#! /bin/bash

echo "Setting up the environment..."

# Install pre-commit package
python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pre-commit

# Install pre-commit hooks if .git directory exists
if [ -d ".git" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    make install-pre-commit-hooks
fi
