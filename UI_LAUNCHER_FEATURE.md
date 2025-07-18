# OpenHands CLI UI Launcher Feature

## Overview

This feature adds a `--ui` flag to the OpenHands CLI that allows users to easily launch the OpenHands UI server using Docker without having to remember the complex Docker command.

## Usage

```bash
openhands --ui
```

This command will:
1. Check if Docker is installed and running
2. Ensure the `~/.openhands` configuration directory exists
3. Pull the required Docker images
4. Launch the OpenHands UI server with the appropriate configuration
5. Make the UI available at http://localhost:3000

## Features

### Docker Requirements Check
- Verifies Docker is installed and available in PATH
- Checks if Docker daemon is running
- Provides helpful error messages with installation links if Docker is not available

### Configuration Sharing
- Uses the same `~/.openhands` directory as the CLI mode
- Settings configured in CLI mode are automatically available in UI mode
- No need to reconfigure API keys or other settings

### Automatic Image Management
- Automatically pulls the correct runtime and application Docker images
- Uses version-specific images matching the installed OpenHands version
- Handles pull failures gracefully with clear error messages

### User-Friendly Output
- Colored terminal output with clear status messages
- Progress indicators for Docker operations
- Helpful instructions for accessing the UI

## Implementation Details

### Files Added/Modified

1. **`openhands/cli/ui_launcher.py`** (new)
   - Contains the main UI launcher functionality
   - Docker requirements checking
   - Configuration directory management
   - Docker command execution

2. **`openhands/core/config/utils.py`** (modified)
   - Added `--ui` flag to argument parser

3. **`openhands/cli/main.py`** (modified)
   - Added UI launcher integration
   - Early exit when `--ui` flag is used

4. **`tests/unit/test_cli_ui_launcher.py`** (new)
   - Comprehensive test suite for UI launcher functionality
   - Tests Docker requirements checking
   - Tests configuration directory handling
   - Tests various failure scenarios

5. **`tests/unit/test_cli.py`** (modified)
   - Added test for CLI integration with `--ui` flag

### Docker Command Generated

The feature generates and executes the following Docker command:

```bash
docker run -it --rm --pull=always \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:{version}-nikolaik \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.openhands:/.openhands \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name openhands-app \
    docker.all-hands.dev/all-hands-ai/openhands:{version}
```

Where `{version}` is automatically determined from the installed OpenHands version.

### Error Handling

The feature includes robust error handling for:
- Docker not installed
- Docker daemon not running
- Docker image pull failures
- Docker container startup failures
- User interruption (Ctrl+C)

### Configuration Directory

The feature ensures the `~/.openhands` directory exists and is properly mounted into the Docker container, allowing:
- Sharing of LLM API keys between CLI and UI modes
- Persistence of user preferences
- Consistent configuration across different usage modes

## Testing

The feature includes comprehensive tests covering:
- Docker requirements checking (success and failure cases)
- Configuration directory management
- UI launcher functionality (dry run and actual execution)
- CLI integration
- Error handling scenarios

Run tests with:
```bash
python -m pytest tests/unit/test_cli_ui_launcher.py -v
python -m pytest tests/unit/test_cli.py::test_main_with_ui_flag -v
```

## Benefits

1. **Simplified User Experience**: Users no longer need to remember or copy complex Docker commands
2. **Consistent Configuration**: Settings are shared between CLI and UI modes
3. **Automatic Version Management**: Always uses the correct Docker images for the installed version
4. **Robust Error Handling**: Clear error messages help users troubleshoot issues
5. **Easy Access**: Single command to launch the full OpenHands UI experience

## Future Enhancements

Potential future improvements could include:
- Support for custom ports via command line arguments
- Integration with different Docker registries
- Support for custom runtime images
- Advanced configuration options for power users
