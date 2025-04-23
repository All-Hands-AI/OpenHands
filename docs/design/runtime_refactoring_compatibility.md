# Runtime Refactoring: Compatibility Considerations

This document addresses specific compatibility concerns for the refactored runtime build approach, particularly focusing on Chromium and tmux.

## Chromium Compatibility

### Challenges

Chromium presents several compatibility challenges when moved to a `/openhands` directory:

1. **Path Dependencies**: Chromium often has hardcoded paths and expects to find resources in specific locations
2. **Library Dependencies**: Chromium depends on numerous system libraries that must be available
3. **Sandbox Requirements**: Chromium's sandbox functionality requires specific permissions and capabilities
4. **User Profile Management**: Chromium stores user profiles in specific locations

### Solutions

Our approach addresses these challenges through:

1. **Complete Bundling**: We copy the entire Playwright-installed Chromium directory to `/openhands/browser/ms-playwright`
2. **Library Bundling**: We identify and copy all required shared libraries to `/openhands/lib`
3. **Environment Variables**: We set `PLAYWRIGHT_BROWSERS_PATH` to point to our custom location
4. **Wrapper Script**: We create an `oh-chromium` wrapper script that:
   - Sets up the correct environment variables
   - Finds the Chromium executable in our custom location
   - Executes Chromium with all necessary arguments

### Implementation Details

The wrapper script (`oh-chromium`) handles the environment setup:

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

During the build process, we:

1. Install Playwright and Chromium in the standard location
2. Copy the entire Chromium installation to `/openhands/browser/ms-playwright`
3. Identify all library dependencies using `ldd` and copy them to `/openhands/lib`

## tmux Compatibility

### Challenges

tmux presents different compatibility challenges:

1. **Socket Location**: tmux creates sockets in specific locations
2. **Configuration Files**: tmux looks for configuration files in the user's home directory
3. **Library Dependencies**: tmux depends on several system libraries
4. **Terminal Capabilities**: tmux requires specific terminal capabilities

### Solutions

Our approach addresses these challenges through:

1. **Binary Copying**: We copy the tmux binary to `/openhands/bin`
2. **Library Bundling**: We identify and copy all required shared libraries to `/openhands/lib`
3. **Wrapper Script**: We create an `oh-tmux` wrapper script that:
   - Sets up the correct environment variables
   - Creates necessary directories
   - Executes tmux with all necessary arguments

### Implementation Details

The wrapper script (`oh-tmux`) handles the environment setup:

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

During the build process, we:

1. Copy the tmux binary to `/openhands/bin`
2. Identify all library dependencies using `ldd` and copy them to `/openhands/lib`

## Testing Strategy

To ensure compatibility, we should test:

1. **Basic Functionality**: Verify that Chromium and tmux can be launched
2. **Feature Completeness**: Verify that all required features work correctly
3. **Edge Cases**: Test with various base images and configurations
4. **Performance**: Measure any performance impact from the new approach

### Test Cases for Chromium

1. Launch Chromium and navigate to a website
2. Test with Playwright automation
3. Verify that browser extensions work
4. Test with different user profiles
5. Verify that downloads work correctly

### Test Cases for tmux

1. Create a new tmux session
2. Attach to an existing session
3. Create multiple windows and panes
4. Run long-running commands in tmux
5. Test tmux plugins if used

## Fallback Strategy

If compatibility issues arise that cannot be resolved, we should implement a fallback strategy:

1. **Detect Compatibility Issues**: Add checks to detect when the bundled approach won't work
2. **Fallback to Installation**: If issues are detected, fall back to installing the required packages in the runtime image
3. **Hybrid Approach**: Use the bundled approach for most components, but install specific problematic components directly

## Conclusion

By carefully bundling Chromium and tmux along with their dependencies, and using wrapper scripts to set up the correct environment, we can successfully relocate these tools to the `/openhands` directory while maintaining full functionality.

The key to success is thorough testing with various base images and configurations to ensure compatibility across different environments.