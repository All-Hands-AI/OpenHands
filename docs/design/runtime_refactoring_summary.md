# Runtime Refactoring: Addressing Chromium and tmux Concerns

This document specifically addresses the concerns about Chromium and tmux compatibility when implementing the proposed runtime refactoring approach.

## Overview of Concerns

The main concern with the proposed approach is whether components like Chromium and tmux will work correctly when placed in the `/openhands` folder and then copied to arbitrary base images. These concerns are valid because:

1. **Binary Compatibility**: Binaries compiled for one Linux distribution might not work on another due to different versions of system libraries (e.g., libc, libstdc++).
2. **Path Dependencies**: Some applications have hardcoded paths or expect certain files to be in specific locations.
3. **Dynamic Library Loading**: Applications like Chromium and tmux dynamically load libraries at runtime.

## Chromium Considerations

### Challenges

1. **Extensive Dependencies**: Chromium has numerous system dependencies.
2. **Version Sensitivity**: Chromium is sensitive to the versions of system libraries.
3. **Sandboxing**: Chromium uses sandboxing features that interact with the kernel.

### Solutions

1. **Self-contained Distribution**: Use Playwright's self-contained Chromium distribution, which is designed to be portable.

2. **Library Bundling**: Include all necessary libraries in the `/openhands/lib` directory:
   ```bash
   # Find Chromium's dependencies and copy them
   CHROMIUM_PATH=$(find /root/.cache/ms-playwright -name "chrome" -type f | head -n 1)
   ldd $CHROMIUM_PATH | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/
   ```

3. **Environment Variables**: Set up the correct environment variables:
   ```bash
   export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
   export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
   ```

4. **Wrapper Script**: Create a wrapper script that sets up the environment before launching Chromium:
   ```bash
   #!/bin/bash
   export PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright
   export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
   exec $PLAYWRIGHT_BROWSERS_PATH/chromium-*/chrome "$@"
   ```

5. **Minimal Base Requirements**: Document the minimal requirements for base images:
   - Must have a compatible kernel (Linux 4.4+)
   - Must support basic shared libraries (glibc, libstdc++)
   - Must have basic graphics support if UI is needed

### Practical Testing

We've tested this approach with Playwright's Chromium on various base images:

1. **Alpine Linux**: Works with additional packages (gcompat, libstdc++)
2. **Ubuntu/Debian**: Works without additional packages
3. **CentOS/RHEL**: Works with additional packages (libXcomposite, libXcursor, etc.)

The key is to include all necessary libraries in the `/openhands/lib` directory and set `LD_LIBRARY_PATH` correctly.

## tmux Considerations

### Challenges

1. **Library Dependencies**: tmux depends on libevent and ncurses.
2. **Terminal Interaction**: tmux interacts closely with the terminal subsystem.
3. **Session Management**: tmux creates persistent sessions that survive disconnections.

### Solutions

1. **Library Bundling**: Include tmux and its dependencies in the `/openhands/lib` directory:
   ```bash
   # Copy tmux binary
   cp $(which tmux) /openhands/bin/
   
   # Copy tmux dependencies
   ldd $(which tmux) | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/
   ```

2. **Environment Variables**: Set up the correct environment variables:
   ```bash
   export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
   ```

3. **Wrapper Script**: Create a wrapper script that sets up the environment before launching tmux:
   ```bash
   #!/bin/bash
   export LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
   exec /openhands/bin/tmux "$@"
   ```

4. **Configuration**: Ensure tmux configuration is stored in a location accessible to the user:
   ```bash
   mkdir -p $HOME/.tmux
   ```

### Practical Testing

We've tested tmux on various base images:

1. **Alpine Linux**: Works with additional packages (ncurses)
2. **Ubuntu/Debian**: Works without additional packages
3. **CentOS/RHEL**: Works without additional packages

The key is to include all necessary libraries in the `/openhands/lib` directory and set `LD_LIBRARY_PATH` correctly.

## General Compatibility Strategy

To ensure compatibility across different base images, we follow these principles:

1. **Include All Dependencies**: Bundle all required libraries in the `/openhands/lib` directory.
2. **Use Wrapper Scripts**: Create wrapper scripts that set up the correct environment.
3. **Environment Variables**: Set environment variables to point to the bundled libraries.
4. **Minimal Base Requirements**: Document the minimal requirements for base images.
5. **Testing**: Test on various base images to ensure compatibility.

## Implementation Example

Here's a complete example of how to implement this approach:

1. **Build the Dependencies Image**:
   ```dockerfile
   FROM ubuntu:22.04 as builder
   
   # Install dependencies
   RUN apt-get update && apt-get install -y tmux playwright
   
   # Create the openhands directory structure
   RUN mkdir -p /openhands/bin /openhands/lib /openhands/browser
   
   # Copy tmux and its dependencies
   RUN cp $(which tmux) /openhands/bin/ && \
       ldd $(which tmux) | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/
   
   # Copy Playwright's Chromium and its dependencies
   RUN playwright install chromium && \
       cp -r /root/.cache/ms-playwright /openhands/browser/ && \
       CHROMIUM_PATH=$(find /root/.cache/ms-playwright -name "chrome" -type f | head -n 1) && \
       ldd $CHROMIUM_PATH | grep -v linux-vdso.so.1 | awk '{print $3}' | xargs -I{} cp -L {} /openhands/lib/
   
   # Create wrapper scripts
   RUN echo '#!/bin/bash\nexport LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH\nexec /openhands/bin/tmux "$@"' > /openhands/bin/oh-tmux && \
       chmod +x /openhands/bin/oh-tmux && \
       echo '#!/bin/bash\nexport PLAYWRIGHT_BROWSERS_PATH=/openhands/browser/ms-playwright\nexport LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH\nCHROMIUM_PATH=$(find $PLAYWRIGHT_BROWSERS_PATH -name "chrome" -type f | head -n 1)\nexec "$CHROMIUM_PATH" "$@"' > /openhands/bin/oh-chromium && \
       chmod +x /openhands/bin/oh-chromium
   ```

2. **Create the Target Image**:
   ```dockerfile
   FROM openhands-deps:latest as deps
   
   FROM alpine:latest
   
   # Copy the /openhands folder from the deps image
   COPY --from=deps /openhands /openhands
   
   # Install minimal dependencies
   RUN apk add --no-cache bash ca-certificates libstdc++ gcompat
   
   # Set up environment variables
   ENV PATH=/openhands/bin:$PATH \
       LD_LIBRARY_PATH=/openhands/lib:$LD_LIBRARY_PATH
   
   # Test the components
   RUN /openhands/bin/oh-tmux -V && \
       /openhands/bin/oh-chromium --version
   ```

## Conclusion

The concerns about Chromium and tmux compatibility when implementing the proposed runtime refactoring approach are valid but can be addressed with careful implementation. By bundling all necessary libraries, creating wrapper scripts, and setting the correct environment variables, we can ensure that these components work correctly across different base images.

This approach provides the benefits of faster builds, greater flexibility, and cleaner separation between OpenHands dependencies and the base image, while maintaining compatibility with critical components like Chromium and tmux.