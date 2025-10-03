.PHONY: help install install-dev test format clean run

# Default target
help:
	@echo "OpenHands CLI - Available commands:"
	@echo "  install                  - Install the package"
	@echo "  install-dev              - Install with development dependencies"
	@echo "  test                     - Run tests"
	@echo "  format                   - Format code with ruff"
	@echo "  clean                    - Clean build artifacts"
	@echo "  run                      - Run the CLI"

# Install the package
install:
	uv sync

# Install with development dependencies
install-dev:
	uv sync --group dev

# Run tests
test:
	uv run pytest

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
	uv run openhands

# Install UV if not present
install-uv:
	@if ! command -v uv &> /dev/null; then \
		echo "Installing UV..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "UV is already installed"; \
	fi
