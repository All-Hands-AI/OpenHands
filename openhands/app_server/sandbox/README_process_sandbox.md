# ProcessSandboxService

The `ProcessSandboxService` is a new implementation of the `SandboxService` interface that creates sandboxes by spawning separate agent server processes. Each sandbox runs as a separate Python process with its own user context and working directory.

## Features

- **Process Isolation**: Each sandbox runs as a separate Python process
- **User Isolation**: Processes can run as different users (configurable)
- **Directory Isolation**: Each sandbox gets its own working directory
- **Port Management**: Automatic port allocation for each sandbox
- **Process Lifecycle**: Full control over process start, pause, resume, and termination
- **Health Monitoring**: Built-in health checking and status monitoring

## Configuration

To use the ProcessSandboxService, set the `RUNTIME` environment variable to `process`:

```bash
export RUNTIME=process
```

### Configuration Options

The `ProcessSandboxServiceInjector` supports the following configuration options:

- `base_working_dir`: Base directory for sandbox working directories (default: `/tmp/openhands-sandboxes`)
- `base_port`: Base port number for agent servers (default: `8000`)
- `python_executable`: Python executable to use for agent processes (default: current Python executable)
- `action_server_module`: Python module for the action execution server (default: `openhands.runtime.action_execution_server`)
- `default_user`: Default user to run sandbox processes as (default: `openhands`)
- `health_check_path`: Health check endpoint path (default: `/alive`)

### Example Configuration

```python
from openhands.app_server.sandbox.process_sandbox_service import ProcessSandboxServiceInjector

injector = ProcessSandboxServiceInjector(
    base_working_dir='/custom/sandbox/path',
    base_port=9000,
    default_user='sandbox_user',
    health_check_path='/health'
)
```

## How It Works

1. **Sandbox Creation**: When a new sandbox is requested, the service:
   - Generates a unique sandbox ID and session API key
   - Creates a dedicated working directory for the sandbox
   - Finds an available port for the agent server
   - Spawns a new Python process running the action execution server

2. **Process Management**: The service tracks all running processes and provides:
   - Process status monitoring using `psutil`
   - Health checking via HTTP requests to the agent server
   - Process lifecycle management (start, pause, resume, terminate)

3. **User Switching**: If configured to run as a specific user, the service:
   - Uses `subprocess.Popen` with `preexec_fn` to switch users
   - Sets appropriate directory ownership and permissions
   - Falls back gracefully if user switching fails

4. **Cleanup**: When a sandbox is deleted, the service:
   - Gracefully terminates the process (with fallback to force kill)
   - Removes the working directory
   - Cleans up internal tracking data

## Security Considerations

- **User Isolation**: Running processes as different users provides process-level isolation
- **Directory Permissions**: Each sandbox directory is owned by the specified user
- **Process Limits**: The service respects system process limits and resource constraints
- **API Keys**: Each sandbox has its own unique session API key for authentication

## Limitations

- **Platform Support**: User switching requires Unix-like systems (Linux, macOS)
- **Permissions**: May require elevated privileges to switch users
- **Resource Usage**: Each sandbox consumes a separate Python process
- **Persistence**: Process state is not persisted across service restarts

## Usage Example

```python
# The service is automatically configured when RUNTIME=process
# and can be used through the standard sandbox API endpoints:

# Start a new sandbox
POST /api/v1/sandboxes

# List sandboxes
GET /api/v1/sandboxes/search

# Get sandbox info
GET /api/v1/sandboxes?id=sandbox_id

# Pause a sandbox
POST /api/v1/sandboxes/{sandbox_id}/pause

# Resume a sandbox
POST /api/v1/sandboxes/{sandbox_id}/resume

# Delete a sandbox
DELETE /api/v1/sandboxes/{sandbox_id}
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: If you get permission errors when switching users, ensure the service is running with appropriate privileges.

2. **Port Already in Use**: If ports are already in use, the service will automatically find the next available port.

3. **User Not Found**: If the specified user doesn't exist, the service will fall back to the current user with a warning.

4. **Process Won't Start**: Check the logs for detailed error messages from the subprocess execution.

### Debugging

Enable debug logging to see detailed process management information:

```bash
export LOG_LEVEL=DEBUG
```

This will show process creation, status changes, and cleanup operations in the logs.
