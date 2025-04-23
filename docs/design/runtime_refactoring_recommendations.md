# Runtime Refactoring: Recommendations

Based on our analysis of the current OpenHands runtime building procedure and the proposed refactoring approach, we recommend implementing the two-stage build process as outlined in the design documents. This document summarizes our findings and provides specific recommendations for implementation.

## Summary of Findings

1. **Current Approach Limitations**:
   - Slow build times, especially when building from scratch
   - Redundant installation of dependencies for each new image
   - Limited reuse of intermediate layers

2. **Proposed Approach Benefits**:
   - Faster builds by reusing the pre-built dependencies image
   - Greater flexibility in choosing base images
   - Better separation of concerns between dependencies and runtime
   - Improved maintainability

3. **Technical Feasibility**:
   - The approach is technically feasible, as demonstrated in the proof-of-concept
   - Compatibility concerns with Chromium and tmux can be addressed through wrapper scripts and library bundling
   - The approach works with various base images, including Alpine, Ubuntu, and Debian

## Implementation Recommendations

### 1. Two-Stage Build Process

Implement the two-stage build process as outlined in the design documents:

1. **Dependencies Image**: Build an intermediate image containing all dependencies in `/openhands`
2. **Runtime Image**: Create the final runtime image by copying `/openhands` from the dependencies image

### 2. Wrapper Scripts

Create wrapper scripts for all tools that need to be relocated to `/openhands`:

- `oh-tmux`: Wrapper for tmux
- `oh-chromium`: Wrapper for Chromium
- `oh-playwright`: Wrapper for Playwright
- `oh-python`: Wrapper for Python
- `oh-action-execution-server`: Wrapper for the action execution server
- `oh-init`: Script to initialize the environment

These scripts should set up the necessary environment variables before executing the binaries.

### 3. Library Bundling

Bundle all necessary libraries in `/openhands/lib` to ensure compatibility across different base images:

1. Identify library dependencies using `ldd`
2. Copy all required libraries to `/openhands/lib`
3. Set `LD_LIBRARY_PATH` to include `/openhands/lib`

### 4. Environment Variables

Set up the necessary environment variables in the runtime image:

```bash
ENV PATH=/openhands/bin:$PATH \
    LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH \
    POETRY_VIRTUALENVS_PATH=/openhands/poetry \
    MAMBA_ROOT_PREFIX=/openhands/micromamba \
    PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright \
    OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
```

### 5. Tagging System

Extend the current tagging system to include information about the dependencies image:

1. **Dependencies Tag**: `oh_deps_v{openhands_version}_{16_digit_hash}`
2. **Runtime Tag**: `oh_v{openhands_version}_{base_image}_{16_digit_deps_hash}`

This allows for efficient caching and reuse of both the dependencies and runtime images.

### 6. Backward Compatibility

Maintain backward compatibility with the current approach:

1. Add a configuration option to choose between the traditional and new approaches
2. Default to the traditional approach for existing users
3. Provide documentation on how to migrate to the new approach

### 7. Testing Strategy

Implement a comprehensive testing strategy:

1. Test with various base images (Ubuntu, Alpine, Debian, CentOS)
2. Test all components (Chromium, tmux, Python, Playwright)
3. Test with different configurations and plugins
4. Measure performance improvements in build time and image size

## Implementation Plan

1. **Phase 1: Proof of Concept**
   - Create wrapper scripts
   - Create Dockerfile templates
   - Test with a few base images

2. **Phase 2: Integration**
   - Integrate the approach into the OpenHands codebase
   - Update the build process
   - Add tests

3. **Phase 3: Documentation and Release**
   - Update documentation
   - Create migration guides
   - Release as part of the next OpenHands version

## Conclusion

The proposed runtime refactoring approach offers significant benefits in terms of build speed, flexibility, and maintainability. By implementing the two-stage build process with careful attention to compatibility concerns, OpenHands can provide a more efficient and flexible runtime building procedure while maintaining compatibility with existing workflows.

We recommend proceeding with the implementation as outlined in this document, starting with a proof-of-concept to validate the approach before full integration into the OpenHands codebase.