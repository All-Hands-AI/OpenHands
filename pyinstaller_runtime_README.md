# PyInstaller Runtime for OpenHands

This directory contains the implementation of a PyInstaller-based approach for the OpenHands runtime. This approach bundles all required dependencies of the action_execution_server into a binary, which can then be copied into any base image to make it OpenHands compatible.

## Overview

The traditional runtime building procedure involves installing all dependencies (Python, Node.js, Playwright, etc.) in the target image, which can be time-consuming and may lead to compatibility issues. The PyInstaller approach simplifies this by:

1. Building a standalone binary with PyInstaller that includes all Python dependencies
2. Copying only the binary and necessary browser components to the target runtime image
3. Eliminating the need to install Python and other dependencies in the target image

## How It Works

### 1. Building the Binary

We use PyInstaller to bundle the action_execution_server and all its dependencies into a standalone binary. This can be done in two ways:

#### Option A: Using poetry-pyinstaller-plugin

```bash
# Install the plugin
pip install poetry-pyinstaller-plugin

# Add configuration to pyproject.toml
# [tool.poetry-pyinstaller-plugin]
# version = "6.13.0"
# 
# [tool.poetry-pyinstaller-plugin.scripts]
# action-execution-server = { source = "openhands/runtime/action_execution_server.py", type = "onedir", bundle = false }

# Build the binary
poetry build --format pyinstaller
```

#### Option B: Direct PyInstaller Usage

```bash
# Install PyInstaller
pip install pyinstaller

# Build the binary
pyinstaller --onedir openhands/runtime/action_execution_server.py
```

### 2. Packaging Browser Components

We extract Playwright's Chromium browser and package it for use with the binary:

```bash
# Package the browser
python package_browser.py browser
```

### 3. Building the Runtime Image

We use a modified version of the runtime_build.py script to build the runtime image:

```bash
# Build the runtime image
python runtime_build_pyinstaller.py --base-image ubuntu:22.04
```

## Files

- `pyinstaller_runtime_plan.md`: The implementation plan for the PyInstaller approach
- `package_browser.py`: Script to extract and package the Playwright browser
- `runtime_build_pyinstaller.py`: Modified runtime_build.py that implements the PyInstaller approach
- `openhands/runtime/utils/runtime_templates/Dockerfile.pyinstaller.j2`: Dockerfile template for the PyInstaller approach

## Advantages

1. **Smaller Image Size**: Only the binary and browser components are needed, not all Python dependencies
2. **Faster Builds**: No need to install Python and dependencies in the target image
3. **Better Compatibility**: The binary should work on any Linux distribution with compatible glibc
4. **Simplified Maintenance**: Easier to update the binary independently of the base image

## Limitations

1. **Binary Compatibility**: The binary may not work on all Linux distributions due to glibc version differences
2. **Browser Integration**: Playwright requires Chromium and its dependencies, which may not be available on all images
3. **Plugin System**: The current plugin system might not work with a bundled binary

## Future Work

1. **Improve Binary Compatibility**: Build the binary in a minimal environment for maximum compatibility
2. **Enhance Browser Integration**: Create a more portable browser package
3. **Modify Plugin System**: Update the plugin system to work with the bundled binary