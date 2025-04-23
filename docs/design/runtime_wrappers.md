# Runtime Wrapper Scripts

This document provides examples of wrapper scripts that would be used to ensure binary compatibility when using the proposed runtime refactoring approach.

## Wrapper Scripts

### 1. tmux Wrapper

The tmux wrapper script ensures that tmux can find its required libraries:

```bash
#!/bin/bash
# /openhands/bin/oh-tmux

# Set up environment for tmux
export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH

# Check if we need to create a session directory
if [ ! -d "$HOME/.tmux" ]; then
  mkdir -p "$HOME/.tmux"
fi

# Execute tmux with all arguments passed to this script
exec /openhands/bin/tmux "$@"
```

### 2. Chromium Wrapper

The Chromium wrapper script sets up the environment for Playwright's Chromium:

```bash
#!/bin/bash
# /openhands/bin/oh-chromium

# Set up environment for Chromium
export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH

# Find the Chromium executable
CHROMIUM_PATH=$(find $PLAYWRIGHT_BROWSERS_PATH -name "chrome" -type f | head -n 1)

if [ -z "$CHROMIUM_PATH" ]; then
  echo "Error: Chromium executable not found in $PLAYWRIGHT_BROWSERS_PATH"
  exit 1
fi

# Execute Chromium with all arguments passed to this script
exec "$CHROMIUM_PATH" "$@"
```

### 3. Playwright Wrapper

The Playwright wrapper script ensures Playwright can find the browser:

```bash
#!/bin/bash
# /openhands/bin/oh-playwright

# Set up environment for Playwright
export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
export PATH=/openhands/micromamba/envs/openhands/bin:$PATH

# Execute Playwright with all arguments passed to this script
exec /openhands/micromamba/bin/micromamba run -n openhands poetry run playwright "$@"
```

### 4. Python Wrapper

The Python wrapper script ensures the correct Python environment is used:

```bash
#!/bin/bash
# /openhands/bin/oh-python

# Set up environment for Python
export PATH=/openhands/micromamba/bin:$PATH
export MAMBA_ROOT_PREFIX=/openhands/micromamba
export POETRY_VIRTUALENVS_PATH=/openhands/poetry

# Execute Python with all arguments passed to this script
exec /openhands/micromamba/bin/micromamba run -n openhands poetry run python "$@"
```

### 5. Action Execution Server Wrapper

The Action Execution Server wrapper script sets up the environment and starts the server:

```bash
#!/bin/bash
# /openhands/bin/oh-action-execution-server

# Set up environment
export PATH=/openhands/micromamba/bin:$PATH
export MAMBA_ROOT_PREFIX=/openhands/micromamba
export POETRY_VIRTUALENVS_PATH=/openhands/poetry
export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH

# Default values
PORT=${1:-8000}
WORKING_DIR=${2:-/workspace}
PLUGINS=${3:-""}

# Build the command
CMD="/openhands/micromamba/bin/micromamba run -n openhands poetry run python -m openhands.runtime.action_execution_server $PORT --working-dir $WORKING_DIR"

# Add plugins if specified
if [ -n "$PLUGINS" ]; then
  CMD="$CMD --plugins $PLUGINS"
fi

# Execute the command
exec $CMD
```

## Library Management

To ensure all required libraries are included, we need to identify and copy the dependencies of each binary:

```bash
#!/bin/bash
# Script to identify and copy library dependencies

# Create the lib directory
mkdir -p /openhands/lib

# Function to copy dependencies
copy_deps() {
  local binary=$1
  echo "Copying dependencies for $binary"
  
  # Get all dependencies
  ldd $binary | grep -v linux-vdso.so.1 | awk '{print $3}' | while read lib; do
    if [ -n "$lib" ] && [ -f "$lib" ]; then
      cp -L $lib /openhands/lib/
      echo "  Copied $lib"
    fi
  done
}

# Copy dependencies for tmux
copy_deps $(which tmux)

# Copy dependencies for Chromium
CHROMIUM_PATH=$(find /root/.cache/ms-playwright -name "chrome" -type f | head -n 1)
if [ -n "$CHROMIUM_PATH" ]; then
  copy_deps $CHROMIUM_PATH
  
  # Chromium has many dependencies, so we need to recursively copy them
  find /openhands/lib -type f -exec ldd {} \; 2>/dev/null | grep -v linux-vdso.so.1 | awk '{print $3}' | sort | uniq | while read lib; do
    if [ -n "$lib" ] && [ -f "$lib" ] && [ ! -f "/openhands/lib/$(basename $lib)" ]; then
      cp -L $lib /openhands/lib/
      echo "  Copied $lib (recursive)"
    fi
  done
fi
```

## Environment Setup

To ensure the environment is properly set up in any base image, we create an initialization script:

```bash
#!/bin/bash
# /openhands/bin/oh-init

# Set up environment variables
export PATH=/openhands/bin:$PATH
export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
export POETRY_VIRTUALENVS_PATH=/openhands/poetry
export MAMBA_ROOT_PREFIX=/openhands/micromamba
export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
export OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server

# Create the openhands user if it doesn't exist
if ! id -u openhands > /dev/null 2>&1; then
  echo "Creating openhands user..."
  if command -v useradd > /dev/null 2>&1; then
    # For Debian/Ubuntu-based systems
    groupadd -g 1000 openhands 2>/dev/null || true
    useradd -u 1000 -g 1000 -m -s /bin/bash openhands 2>/dev/null || true
  elif command -v adduser > /dev/null 2>&1; then
    # For Alpine-based systems
    addgroup -g 1000 openhands 2>/dev/null || true
    adduser -D -u 1000 -G openhands openhands 2>/dev/null || true
  fi
fi

# Create and set permissions for workspace directory
mkdir -p /workspace
chown -R openhands:openhands /workspace /openhands 2>/dev/null || true

echo "OpenHands environment initialized successfully!"
```

## Integration with Docker

To integrate these wrapper scripts with Docker, we modify the Dockerfile to include them:

```dockerfile
FROM openhands-deps:latest as deps

FROM alpine:latest

# Copy the /openhands folder from the deps image
COPY --from=deps /openhands /openhands

# Set up environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH

# Install minimal dependencies required by the base system
RUN apk add --no-cache bash ca-certificates libstdc++ gcompat

# Initialize the OpenHands environment
RUN /openhands/bin/oh-init

# Set the working directory
WORKDIR /workspace

# Switch to the openhands user
USER openhands

# Command to start the action execution server
CMD ["/openhands/bin/oh-action-execution-server", "8000", "/workspace"]
```

## Conclusion

These wrapper scripts and environment setup procedures ensure that the OpenHands runtime components can work correctly in any base image. By properly managing library dependencies and environment variables, we can achieve binary compatibility across different Linux distributions.

The key advantages of this approach are:

1. **Portability**: The same `/openhands` folder can be used with any base image
2. **Isolation**: All OpenHands-specific components are contained within the `/openhands` folder
3. **Flexibility**: Easy to update or modify individual components without rebuilding the entire image
4. **Efficiency**: Faster builds by reusing the pre-built dependencies image