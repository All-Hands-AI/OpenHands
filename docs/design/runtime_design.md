# Runtime Building Procedure Design

## Architecture Overview

The OpenHands Docker Runtime is a core component that enables secure and flexible execution of AI agent actions. It creates a sandboxed environment using Docker, where arbitrary code can be run safely without risking the host system.

### Traditional Building Process

The traditional runtime building procedure follows these steps:

1. **Base Image Selection**: Takes a base image (e.g., `nikolaik/python-nodejs:python3.12-nodejs22`)
2. **Image Building**: Builds a new Docker image on top of it with OpenHands-specific code and dependencies
3. **Tagging System**: Uses a sophisticated tagging system to optimize rebuilds:
   - **Source Tag** (`oh_v{version}_{lock_hash}_{source_hash}`): Most specific, includes source code hash
   - **Lock Tag** (`oh_v{version}_{lock_hash}`): Based on dependencies and base image
   - **Versioned Tag** (`oh_v{version}_{base_image}`): Most generic, based on OpenHands version and base image

4. **Dependency Installation**:
   - System dependencies via apt-get (including tmux, git, etc.)
   - Python dependencies via poetry and micromamba
   - Chromium via playwright install
   - VSCode server
   - Other tools and configurations

5. **Optimization Strategies**:
   - Reusing existing images when possible
   - Caching dependencies
   - Building in layers

### Key Components

1. **Action Execution Server**: Runs inside the Docker container and executes actions received from the OpenHands backend
2. **Browser Environment**: Uses Chromium installed via Playwright
3. **Bash Session**: Uses tmux for persistent terminal sessions
4. **Plugin System**: Supports extensions like Jupyter notebooks

## Two-Stage Building Approach

### Overview

The two-stage approach simplifies the runtime building procedure by:

1. Building all dependencies into an intermediate Docker image with everything in `/openhands` folder
2. For any arbitrary base image, simply copying the `/openhands` folder to form the final image

### Benefits

1. **Faster Builds**: Significantly reduces build time for new base images
2. **Flexibility**: Makes it easier to use arbitrary base images
3. **Cleaner Separation**: Clear distinction between OpenHands dependencies and the base image
4. **Simplified Maintenance**: Easier to update dependencies independently of the base image
5. **Reduced Duplication**: Avoids rebuilding the same dependencies for different base images

### Challenges and Solutions

#### 1. Binary Compatibility

**Challenge**: Binaries compiled in one environment might not work in another due to different system libraries.

**Solutions**:
- Include all necessary shared libraries in the `/openhands` folder
- Use wrapper scripts that set up the correct environment (LD_LIBRARY_PATH, etc.)
- For critical components like Chromium, include all dependencies in a self-contained manner

#### 2. Chromium Considerations

**Challenge**: Chromium has extensive system dependencies and might not work when simply copied.

**Solutions**:
- Use Playwright's self-contained Chromium distribution
- Include all Chromium dependencies in the `/openhands` folder
- Create a wrapper script that sets up the correct environment variables before launching Chromium
- Consider using container-in-container approach for Chromium if necessary

#### 3. tmux Considerations

**Challenge**: tmux depends on system libraries like libevent and ncurses.

**Solutions**:
- Include tmux and its dependencies in the `/openhands` folder
- Create a wrapper script that sets LD_LIBRARY_PATH to find the included libraries
- Consider statically linking tmux to reduce dependencies

#### 4. Path and Configuration Issues

**Challenge**: Hardcoded paths and configurations might break when moved.

**Solutions**:
- Use relative paths where possible
- Create configuration files at runtime based on the actual environment
- Use environment variables to specify paths instead of hardcoding them

#### 5. Permission Issues

**Challenge**: Copying files might not preserve permissions correctly.

**Solutions**:
- Explicitly set permissions after copying
- Use archive mode when copying to preserve permissions
- Handle user/group IDs consistently across images

## PyInstaller Approach

### Overview

The PyInstaller approach further simplifies the runtime building procedure by:

1. Using PyInstaller to bundle the action_execution_server and all its dependencies into a standalone binary
2. Packaging Playwright's Chromium browser in a portable way
3. Copying only the binary and browser components to the target runtime image
4. Eliminating the need to install Python and other dependencies in the target image

### Benefits

1. **Smaller Image Size**: Only the binary and browser components are needed, not all Python dependencies
2. **Faster Builds**: No need to install Python and dependencies in the target image
3. **Better Compatibility**: The binary should work on any Linux distribution with compatible glibc
4. **Simplified Maintenance**: Easier to update the binary independently of the base image

### Challenges and Solutions

#### 1. Binary Compatibility

**Challenge**: Binaries compiled in one environment might not work in another due to different system libraries.

**Solutions**:
- Build the binary in a minimal environment (e.g., Ubuntu 20.04) for maximum compatibility
- Include all necessary shared libraries in the binary
- Use static linking where possible

#### 2. Browser Integration

**Challenge**: Playwright requires Chromium and its dependencies.

**Solutions**:
- Extract Chromium from Playwright's cache
- Create a portable browser package
- Use wrapper scripts to set up the correct environment

#### 3. Plugin System

**Challenge**: The current plugin system might not work with a bundled binary.

**Solutions**:
- Modify the plugin system to work with the binary
- Include all plugins in the binary
- Implement a mechanism to load plugins at runtime

### Implementation

The implementation consists of three main components:

1. **PyInstaller Binary Builder**: Uses PyInstaller to bundle the action_execution_server and its dependencies
2. **Browser Packager**: Extracts and packages the Playwright browser for use with the binary
3. **Docker Image Builder**: Creates a minimal Docker image with the binary and browser components

## Implementation Plan

### Phase 1: Create PyInstaller Binary

1. Create a PyInstaller spec file for action_execution_server.py
2. Build the binary using PyInstaller
3. Extract and package Playwright's Chromium browser
4. Create a new Dockerfile template for the PyInstaller approach

### Phase 2: Update Runtime Builder

1. Update `runtime_build.py` to implement the PyInstaller approach
2. Add option to build using PyInstaller
3. Implement the copying mechanism for the binary and browser components
4. Simplify the tagging system for better clarity

### Phase 3: Integration and Testing

1. Test with various base images to ensure compatibility
2. Benchmark performance improvements
3. Verify all components work correctly (browser, bash, plugins, etc.)
4. Update documentation

### Phase 4: Optimization

1. Analyze and optimize the size of the binary
2. Implement selective features based on requirements
3. Further improve build performance

## Technical Details

### PyInstaller Binary Structure

```
/openhands/
├── action-execution-server/  # PyInstaller binary
│   ├── action-execution-server  # Main executable
│   ├── _internal/            # PyInstaller bundled dependencies
│   └── ...
├── browser/                  # Packaged Chromium browser
│   ├── ms-playwright/        # Playwright browser files
│   └── chromium-wrapper.sh   # Wrapper script for Chromium
└── lib/                      # Additional shared libraries if needed
```

### Dockerfile Template for PyInstaller Approach

```dockerfile
FROM {{ base_image }}

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

# Create directories
RUN mkdir -p /openhands/bin /openhands/lib /workspace && \
    chown -R openhands:openhands /workspace /openhands 2>/dev/null || true

# Copy the bundled action execution server
COPY ./dist/pyinstaller/action-execution-server /openhands/action-execution-server

# Copy Playwright browser
COPY ./browser /openhands/browser

# Set environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    PLAYWRIGHT_BROWSERS_PATH=/openhands/browser \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set the working directory
WORKDIR /workspace

# Switch to the openhands user
USER openhands

# Command to start the action execution server
CMD ["/openhands/action-execution-server/action-execution-server", "8000", "/workspace"]
```

### Usage

To build a runtime image using the PyInstaller approach:

```bash
python runtime_build_pyinstaller.py --base-image ubuntu:22.04
```

This will:
1. Build the PyInstaller binary
2. Package the Playwright browser
3. Create a Docker image with the binary and browser components

## Conclusion

Both the two-stage building approach and the PyInstaller approach offer significant benefits in terms of build speed, flexibility, and maintainability. The PyInstaller approach provides additional advantages in terms of image size and build simplicity, but may have challenges with plugin support and binary compatibility.

By bundling the action_execution_server and its dependencies into a standalone binary, we can achieve an even more efficient runtime building process that supports a wider range of base images while maintaining the security and isolation properties of the traditional approach.
