# Local Test Setup Guide

This document explains how to set up and run all OpenHands tests and linters locally to match the GitHub Actions workflows.

## Prerequisites

1. **Python 3.12** with Poetry installed
2. **Node.js 20+** with npm
3. **Docker** (for full runtime tests)
4. **tmux** (already installed on most systems)

## Initial Setup

### 1. Install Python Dependencies
```bash
poetry install --with dev,test,runtime
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install --frozen-lockfile
cd ..
```

### 3. Install Pre-commit (if not using Poetry environment)
```bash
pip install pre-commit==3.7.0
```

## Running Tests and Linters

### Quick Test Script
Run all tests and linters at once:
```bash
./run_local_tests.sh
```

### Individual Commands

#### Python Lint
```bash
pre-commit run --all-files --config ./dev_config/python/.pre-commit-config.yaml
```

#### Frontend Lint  
```bash
cd frontend
npm run lint
npm run check-translation-completeness
cd ..
```

#### Python Unit Tests
```bash
poetry run pytest --forked -n auto -svv ./tests/unit
```

#### Runtime Tests
```bash
# CLI Runtime (safest for local development)
TEST_RUNTIME=cli poetry run pytest -svv tests/runtime/test_bash.py

# Or specific test
TEST_RUNTIME=cli poetry run pytest -svv tests/runtime/test_bash.py::test_basic_command
```

## Fixed Issues

### Circular Import Resolution
- **Issue**: `openhands.runtime.base` imported from `openhands.core.config`, which imported from `openhands.runtime.container_reuse_strategy`
- **Fix**: Moved `ContainerReuseStrategy` enum to `openhands.core.config.container_reuse_strategy` to break the circular dependency

### Missing Dependencies
- **Issue**: Tests failed due to missing `kubernetes` package and other dependencies
- **Fix**: Installed all Poetry dependency groups: `--with dev,test,runtime`

### Test Environment Configuration
- **Issue**: Runtime tests require specific environment variables
- **Fix**: Set `TEST_RUNTIME=cli` for safe local testing

## Environment Variables

For runtime tests, you can set these environment variables:
- `TEST_RUNTIME=cli` - Use CLI runtime (safest for local dev)
- `TEST_RUNTIME=docker` - Use Docker runtime (requires Docker)
- `TEST_RUNTIME=local` - Use local runtime
- `RUN_AS_OPENHANDS=True` - Run as openhands user (default)
- `TEST_IN_CI=False` - Indicate not running in CI environment

## Expected Results

### What Should Pass
- ✅ Python lint (pre-commit hooks)
- ✅ Frontend lint and TypeScript compilation
- ✅ Most Python unit tests (800+ tests)
- ✅ Basic runtime tests with CLI runtime

### What May Fail Locally
- ⚠️ Some unit tests requiring specific CI environment setup
- ⚠️ Docker runtime tests if Docker isn't properly configured
- ⚠️ Tests requiring external services or specific networking setup
- ⚠️ Tests with hard-coded CI-specific paths or configuration

## Docker Runtime Tests (Advanced)

To run full Docker runtime tests:
```bash
# Ensure Docker is running
docker info

# Run Docker runtime tests
TEST_RUNTIME=docker poetry run pytest -svv tests/runtime/test_bash.py

# For full runtime test suite (requires more setup)
poetry run pytest tests/runtime/
```

## Troubleshooting

### ffmpeg Warnings
If you see warnings about missing ffmpeg, install it:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

### Permission Issues
If you encounter permission errors with Docker:
```bash
sudo usermod -aG docker $USER
# Then log out and back in
```

### Import Errors
If you see import errors, ensure all dependencies are installed:
```bash
poetry install --with dev,test,runtime
```

## GitHub Actions Equivalent

This local setup matches these GitHub Actions workflows:
- `lint.yml` - Python and frontend linting
- `py-unit-tests.yml` - Python unit tests
- `ghcr-build.yml` - Runtime tests (basic subset)

The full CI environment includes additional Docker image building and deployment steps that aren't necessary for local development.