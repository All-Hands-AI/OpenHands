# Refactored Runtime Building Approach

This document describes the refactored approach to building OpenHands runtime images.

## Overview

The refactored runtime building approach uses a two-stage process:

1. **Dependencies Image**: Build a single image containing all dependencies in the `/openhands` folder
2. **Runtime Image**: For any base image, copy the `/openhands` folder from the dependencies image

This approach offers several advantages:
- Faster build times for new base images
- Smaller final images (no duplicate dependencies)
- Better compatibility with different base images
- Easier maintenance and updates

## How It Works

### Dependencies Image

The dependencies image is built once and contains:
- All Python dependencies installed via Poetry
- Playwright and Chromium
- VSCode Server
- Tmux and other utilities
- Wrapper scripts for compatibility

Everything is installed into the `/openhands` folder, which is self-contained and can be copied to any base image.

### Runtime Image

The runtime image is built by:
1. Starting from any base image
2. Copying the `/openhands` folder from the dependencies image
3. Setting up environment variables to use the tools in `/openhands/bin`
4. Installing minimal dependencies required by the base system

## Wrapper Scripts

To ensure compatibility across different base images, wrapper scripts are provided in `/openhands/bin`:

- `oh-tmux`: Wrapper for tmux with proper library paths
- `oh-chromium`: Wrapper for Chromium with proper library paths
- `oh-playwright`: Wrapper for Playwright
- `oh-python`: Wrapper for Python with proper environment
- `oh-action-execution-server`: Wrapper for the action execution server

## Usage

To build a runtime image using the refactored approach:

```bash
# Build the dependencies image (only needed once)
python -m openhands.runtime.utils.runtime_build --build_deps_only

# Build a runtime image using the dependencies image
python -m openhands.runtime.utils.runtime_build --base_image <base_image> --use_deps_image
```

You can also specify a custom dependencies image:

```bash
python -m openhands.runtime.utils.runtime_build --base_image <base_image> --use_deps_image --deps_image <deps_image>
```

## Compatibility Considerations

### Library Dependencies

The wrapper scripts ensure that the correct library paths are set, so tools like tmux and Chromium can find their dependencies in `/openhands/lib`.

### Base Image Requirements

The base image must have:
- Basic shell utilities (bash)
- CA certificates for HTTPS connections
- Compatible architecture (same as the dependencies image)

Most minimal base images (Alpine, Debian, Ubuntu) already meet these requirements.

## Implementation Details

The implementation consists of:

1. New Dockerfile templates:
   - `Dockerfile.deps.j2`: Template for building the dependencies image
   - `Dockerfile.runtime.j2`: Template for building the runtime image

2. Wrapper scripts in `/openhands/bin`:
   - Ensure proper environment variables and library paths
   - Handle compatibility issues across different base images

3. Updated build process:
   - New `BuildFromImageType.DEPS` option
   - Functions to build and use the dependencies image
   - CLI options to control the build process