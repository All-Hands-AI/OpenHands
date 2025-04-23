# Runtime Building Procedure Refactoring

## Current Architecture

The OpenHands Docker Runtime is a core component that enables secure and flexible execution of AI agent actions. It creates a sandboxed environment using Docker, where arbitrary code can be run safely without risking the host system.

### Current Building Process

The current runtime building procedure follows these steps:

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

## Proposed Refactoring Approach

### Overview

The proposed approach aims to simplify the runtime building procedure by:

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

## Implementation Plan

### Phase 1: Create Base Dependencies Image

1. Create a Dockerfile that installs all dependencies to `/openhands`
2. Include all necessary libraries and binaries
3. Create wrapper scripts for key components (Chromium, tmux, etc.)
4. Test the image with various base images to ensure compatibility

### Phase 2: Modify Runtime Builder

1. Update `runtime_build.py` to support the new building approach
2. Add option to use the dependencies-only image
3. Implement the copying mechanism for the `/openhands` folder
4. Maintain backward compatibility with the current approach

### Phase 3: Integration and Testing

1. Test with various base images to ensure compatibility
2. Benchmark performance improvements
3. Verify all components work correctly (browser, bash, plugins, etc.)
4. Update documentation

### Phase 4: Optimization

1. Analyze and optimize the size of the `/openhands` folder
2. Implement selective copying based on required features
3. Further improve build performance

## Technical Details

### Dependencies Image Structure

```
/openhands/
├── bin/                  # Executable wrappers
├── lib/                  # Shared libraries
├── micromamba/           # Micromamba environment
├── poetry/               # Poetry virtual environments
├── code/                 # OpenHands source code
├── .openvscode-server/   # VSCode server
├── browser/              # Chromium and dependencies
└── workspace/            # Default workspace directory
```

### Wrapper Script Example

```bash
#!/bin/bash
# Wrapper for Chromium

# Set up environment
export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
export CHROMIUM_PATH=/openhands/browser/chromium

# Launch Chromium with the correct environment
exec $CHROMIUM_PATH "$@"
```

### Modified Dockerfile Template

```dockerfile
# Stage 1: Build the dependencies image
FROM {{ base_image }} as deps
# Install all dependencies to /openhands
# ...

# Stage 2: Final image
FROM {{ target_base_image }}
# Copy the /openhands folder from the deps image
COPY --from=deps /openhands /openhands

# Set up environment variables
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    # ... other environment variables
```

## Conclusion

The proposed refactoring approach offers significant benefits in terms of build speed, flexibility, and maintainability. While there are challenges related to binary compatibility and system dependencies, these can be addressed with careful implementation of wrapper scripts and proper environment setup.

By separating the OpenHands dependencies from the base image, we can achieve a more modular and efficient runtime building process that supports a wider range of base images while maintaining the security and isolation properties of the current approach.