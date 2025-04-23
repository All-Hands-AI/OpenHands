# Runtime Refactoring Implementation Plan

This document outlines the implementation plan for refactoring the OpenHands runtime building procedure to use a more efficient approach with intermediate images.

## Current Architecture

The current OpenHands runtime building procedure:

1. Takes a base image (e.g., `ubuntu:22.04` or `nikolaik/python-nodejs:python3.12-nodejs22`)
2. Builds a complete runtime image by:
   - Installing system dependencies
   - Setting up micromamba and Python
   - Installing Python dependencies with Poetry
   - Installing Playwright and Chromium
   - Setting up VSCode Server
   - Copying OpenHands source code

This approach has several limitations:
- Slow build times, especially when building from scratch
- Redundant installation of dependencies for each new image
- Limited reuse of intermediate layers

## Proposed Architecture

The proposed architecture introduces a two-stage build process:

1. **Dependencies Image**: Build an intermediate image containing all dependencies
   - All dependencies are installed in a `/openhands` directory
   - This includes system packages, Python libraries, Playwright, Chromium, tmux, etc.
   - This image is built once and can be reused

2. **Runtime Image**: Create the final runtime image by:
   - Starting from any arbitrary base image
   - Copying the `/openhands` directory from the dependencies image
   - Setting up necessary environment variables and paths

### Implementation Details

#### 1. Dependencies Image Dockerfile

```dockerfile
FROM ubuntu:22.04 as builder

# Set up environment variables
ENV POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install base system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl ca-certificates sudo apt-utils git jq tmux build-essential ripgrep \
        libgl1-mesa-glx libasound2-plugins libatomic1 && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    TZ=Etc/UTC DEBIAN_FRONTEND=noninteractive \
        apt-get install -y --no-install-recommends nodejs python3.12 python-is-python3 python3-pip python3.12-venv && \
    corepack enable yarn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /openhands/bin /openhands/lib /openhands/poetry /openhands/micromamba

# Install micromamba
RUN mkdir -p /openhands/micromamba/bin && \
    /bin/bash -c "PREFIX_LOCATION=/openhands/micromamba BIN_FOLDER=/openhands/micromamba/bin INIT_YES=no CONDA_FORGE_YES=yes $(curl -L https://micro.mamba.pm/install.sh)" && \
    /openhands/micromamba/bin/micromamba config remove channels defaults

# Create the openhands virtual environment and install poetry and python
RUN /openhands/micromamba/bin/micromamba create -n openhands -y && \
    /openhands/micromamba/bin/micromamba install -n openhands -c conda-forge poetry python=3.12 -y

# Create a clean openhands directory for dependencies
RUN mkdir -p /openhands/code/openhands && \
    touch /openhands/code/openhands/__init__.py

# Copy dependency files
COPY ./code/pyproject.toml ./code/poetry.lock /openhands/code/

# Configure micromamba and poetry
RUN /openhands/micromamba/bin/micromamba config set changeps1 False && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry config virtualenvs.path /openhands/poetry && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry env use python3.12

# Install project dependencies
RUN /openhands/micromamba/bin/micromamba run -n openhands poetry install --only main --no-interaction --no-root && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry install --only runtime --no-interaction --no-root

# Install playwright and its dependencies
RUN apt-get update && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry run pip install playwright && \
    /openhands/micromamba/bin/micromamba run -n openhands poetry run playwright install --with-deps chromium

# Copy Chromium to a specific location
RUN mkdir -p /openhands/browser && \
    cp -r /root/.cache/ms-playwright /openhands/browser/

# Create wrapper scripts
COPY ./code/openhands/runtime/utils/wrappers/* /openhands/bin/
RUN chmod +x /openhands/bin/*

# Copy library dependencies
RUN mkdir -p /openhands/lib && \
    ldd $(which tmux) | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/ && \
    CHROMIUM_PATH=$(find /openhands/browser/ms-playwright -name "chrome" -type f | head -n 1) && \
    ldd $CHROMIUM_PATH | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/

# Clear caches
RUN /openhands/micromamba/bin/micromamba run -n openhands poetry cache clear --all . -n && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    /openhands/micromamba/bin/micromamba clean --all
```

#### 2. Runtime Image Dockerfile

```dockerfile
ARG BASE_IMAGE
FROM openhands-deps:latest as deps
FROM ${BASE_IMAGE}

# Copy the /openhands folder from the deps image
COPY --from=deps /openhands /openhands

# Set up environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install minimal dependencies required by the base system
RUN if command -v apt-get > /dev/null; then \
        apt-get update && apt-get install -y --no-install-recommends ca-certificates bash && \
        apt-get clean && rm -rf /var/lib/apt/lists/*; \
    elif command -v apk > /dev/null; then \
        apk add --no-cache ca-certificates bash gcompat libstdc++; \
    elif command -v yum > /dev/null; then \
        yum install -y ca-certificates bash; \
        yum clean all; \
    fi

# Create the openhands user if it doesn't exist
RUN if ! id -u openhands > /dev/null 2>&1; then \
        if command -v useradd > /dev/null 2>&1; then \
            groupadd -g 1000 openhands 2>/dev/null || true; \
            useradd -u 1000 -g 1000 -m -s /bin/bash openhands 2>/dev/null || true; \
        elif command -v adduser > /dev/null 2>&1; then \
            addgroup -g 1000 openhands 2>/dev/null || true; \
            adduser -D -u 1000 -G openhands openhands 2>/dev/null || true; \
        fi; \
    fi

# Create and set permissions for workspace directory
RUN mkdir -p /workspace && \
    chown -R openhands:openhands /workspace /openhands 2>/dev/null || true

# Set the working directory
WORKDIR /workspace

# Switch to the openhands user
USER openhands

# Command to start the action execution server
CMD ["/openhands/bin/oh-action-execution-server", "8000", "/workspace"]
```

#### 3. Wrapper Scripts

Create wrapper scripts in `openhands/runtime/utils/wrappers/` to ensure binary compatibility:

1. `oh-tmux` - Wrapper for tmux
2. `oh-chromium` - Wrapper for Chromium
3. `oh-playwright` - Wrapper for Playwright
4. `oh-python` - Wrapper for Python
5. `oh-action-execution-server` - Wrapper for the action execution server

These scripts will set up the necessary environment variables before executing the binaries.

#### 4. Modified Build Process

Update the `runtime_build.py` file to implement the new build process:

1. Add a new function `build_dependencies_image` to build the intermediate image
2. Modify `build_runtime_image` to use the dependencies image
3. Update the tagging system to include information about the dependencies image

## Implementation Steps

1. Create the wrapper scripts in `openhands/runtime/utils/wrappers/`
2. Create the Dockerfile templates for the dependencies and runtime images
3. Update the `runtime_build.py` file to implement the new build process
4. Add tests to verify the new build process
5. Update documentation to reflect the new approach

## Compatibility Considerations

### Chromium Compatibility

Chromium compatibility is addressed by:
1. Copying all Chromium files to `/openhands/browser/ms-playwright`
2. Copying all required libraries to `/openhands/lib`
3. Setting `LD_LIBRARY_PATH` to include `/openhands/lib`
4. Creating a wrapper script that sets up the environment before launching Chromium

### tmux Compatibility

tmux compatibility is addressed by:
1. Copying the tmux binary to `/openhands/bin`
2. Copying all required libraries to `/openhands/lib`
3. Setting `LD_LIBRARY_PATH` to include `/openhands/lib`
4. Creating a wrapper script that sets up the environment before launching tmux

## Benefits

1. **Faster Builds**: The dependencies image is built once and reused
2. **Smaller Images**: The final runtime image only contains the necessary components
3. **Greater Flexibility**: Any base image can be used for the runtime image
4. **Better Separation of Concerns**: Dependencies are managed separately from the runtime
5. **Improved Maintainability**: Easier to update dependencies without rebuilding the entire image

## Limitations and Considerations

1. **Binary Compatibility**: The dependencies image must be built for the same architecture as the runtime image
2. **Library Compatibility**: Some libraries may have different versions in different base images
3. **Storage Requirements**: The dependencies image may be large (several GB)
4. **Cache Management**: Need to implement proper caching of the dependencies image

## Next Steps

1. Implement a proof-of-concept to validate the approach
2. Test with various base images to ensure compatibility
3. Measure performance improvements in build time and image size
4. Refine the approach based on feedback and testing results