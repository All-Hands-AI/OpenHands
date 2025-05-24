# PyInstaller Runtime Implementation Plan

## Overview

This plan outlines how to implement a PyInstaller-based approach for the OpenHands runtime, which will bundle all required dependencies of the action_execution_server into a binary. This approach will simplify the runtime building procedure by:

1. Building a standalone binary with PyInstaller that includes all Python dependencies
2. Copying only the binary and necessary browser components to the target runtime image
3. Eliminating the need to install Python and other dependencies in the target image

## Implementation Steps

### 1. Build the PyInstaller Binary

#### Option A: Using poetry-pyinstaller-plugin
- Add configuration to pyproject.toml:
  ```toml
  [tool.poetry-pyinstaller-plugin]
  version = "6.13.0"
  
  [tool.poetry-pyinstaller-plugin.scripts]
  action-execution-server = { source = "openhands/runtime/action_execution_server.py", type = "onedir", bundle = false }
  ```
- Run `poetry build` to create the binary

#### Option B: Direct PyInstaller Usage
- Create a spec file for action_execution_server.py
- Run PyInstaller with the spec file
- Ensure all dependencies are included

### 2. Package Browser Components

- Extract Playwright's Chromium browser from the cache
- Create a portable browser package that can be copied to the target image
- Include necessary wrapper scripts for browser execution

### 3. Update Runtime Builder

- Modify `runtime_build.py` to implement the PyInstaller approach
- Add a new build method that uses the PyInstaller binary
- Create a new Dockerfile template for the PyInstaller approach
- Implement the copying mechanism for the binary and browser components

### 4. Create Wrapper Scripts

- Create wrapper scripts for the action_execution_server binary
- Create wrapper scripts for browser execution
- Ensure proper environment variables are set

### 5. Testing

- Test with various base images to ensure compatibility
- Verify all components work correctly (browser, bash, plugins, etc.)
- Benchmark performance improvements

## Advantages

1. **Smaller Image Size**: Only the binary and browser components are needed, not all Python dependencies
2. **Faster Builds**: No need to install Python and dependencies in the target image
3. **Better Compatibility**: The binary should work on any Linux distribution with compatible glibc
4. **Simplified Maintenance**: Easier to update the binary independently of the base image

## Challenges and Solutions

### 1. Binary Compatibility

**Challenge**: Binaries compiled in one environment might not work in another due to different system libraries.

**Solutions**:
- Build the binary in a minimal environment (e.g., Ubuntu 20.04) for maximum compatibility
- Include all necessary shared libraries in the binary
- Use static linking where possible

### 2. Browser Integration

**Challenge**: Playwright requires Chromium and its dependencies.

**Solutions**:
- Extract Chromium from Playwright's cache
- Create a portable browser package
- Use wrapper scripts to set up the correct environment

### 3. Plugin System

**Challenge**: The current plugin system might not work with a bundled binary.

**Solutions**:
- Modify the plugin system to work with the binary
- Include all plugins in the binary
- Implement a mechanism to load plugins at runtime

## Implementation Timeline

1. **Phase 1**: Create and test the PyInstaller binary (1-2 days)
2. **Phase 2**: Package browser components (1 day)
3. **Phase 3**: Update runtime builder (1-2 days)
4. **Phase 4**: Create wrapper scripts (1 day)
5. **Phase 5**: Testing and optimization (2-3 days)

## Conclusion

The PyInstaller approach offers significant benefits in terms of build speed, image size, and compatibility. While there are challenges related to binary compatibility and browser integration, these can be addressed with careful implementation of wrapper scripts and proper environment setup.