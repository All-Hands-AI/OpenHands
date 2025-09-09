.PHONY: help install install-dev test lint format clean run install-pre-commit-hooks

# Default target
help:
	@echo "OpenHands CLI - Available commands:"
	@echo "  install                  - Install the package"
	@echo "  install-dev              - Install with development dependencies"
	@echo "  install-pre-commit-hooks - Install pre-commit hooks"
	@echo "  test                     - Run tests"
	@echo "  lint                     - Run pre-commit on all files"
	@echo "  format                   - Format code with ruff"
	@echo "  clean                    - Clean build artifacts"
	@echo "  run                      - Run the CLI"

# Install the package
install:
	uv sync

# Install with development dependencies
install-dev:
	uv sync --extra dev

# Run tests
test:
	uv run pytest

# Install pre-commit hooks
install-pre-commit-hooks: install-dev
	@echo "Installing pre-commit hooks..."
	@git config --unset-all core.hooksPath || true
	uv run pre-commit install
	@echo "Pre-commit hooks installed successfully."

# Run pre-commit on all files
lint: install-dev
	@echo "Running pre-commit on all files..."
	uv run pre-commit run --all-files --show-diff-on-failure



# Format code
format:
	uv run ruff format openhands_cli/

# Clean build artifacts
clean:
	rm -rf .venv/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the CLI
run:
	uv run openhands-cli

# Install UV if not present
install-uv:
	@if ! command -v uv &> /dev/null; then \
		echo "Installing UV..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "UV is already installed"; \
	fi
