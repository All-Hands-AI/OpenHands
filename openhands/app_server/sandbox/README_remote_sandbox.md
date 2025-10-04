# RemoteSandboxService

The `RemoteSandboxService` provides a way to run sandboxes remotely using HTTP communication with a remote runtime server. This is analogous to the legacy `RemoteRuntime` but adapted to work with the new Sandbox interface.

## Configuration

The service is configured using `RemoteSandboxConfig`:

```python
from openhands.app_server.sandbox.remote_sandbox_service import RemoteSandboxConfig

config = RemoteSandboxConfig(
    remote_runtime_api_url="http://your-runtime-server.com",
    api_key="your-api-key",
    container_url_pattern="http://localhost:{port}",  # Optional
    request_timeout=300  # Optional, defaults to 300 seconds
)
```

## Usage

The service implements the standard `SandboxService` interface:

```python
from openhands.app_server.sandbox.remote_sandbox_service import RemoteSandboxServiceManager

# Create service manager
manager = RemoteSandboxServiceManager(config=config)
service = manager.get_sandbox_service()

# Start a sandbox
sandbox = await service.start_sandbox("your-sandbox-spec-id")

# Get sandbox information
sandbox_info = await service.get_sandbox(sandbox.id)

# Pause/resume sandbox
await service.pause_sandbox(sandbox.id)
await service.resume_sandbox(sandbox.id)

# Delete sandbox
await service.delete_sandbox(sandbox.id)
```

## HTTP Protocol

The service communicates with a remote runtime server using the following endpoints:

- `POST /start` - Start a new runtime/sandbox
- `POST /resume` - Resume a paused runtime
- `POST /pause` - Pause a running runtime
- `POST /stop` - Stop and delete a runtime
- `GET /status` - Get runtime status (used by get_sandbox)

### Authentication

All requests include an `X-API-Key` header with the configured API key.

### Request/Response Format

**Start Request:**
```json
{
  "image": "sandbox-spec-id",
  "environment": {"VAR": "value"},
  "working_dir": "/workspace"
}
```

**Start Response:**
```json
{
  "runtime_id": "runtime-123",
  "url": "http://localhost:8000",
  "work_hosts": {"host1": 8001},
  "session_api_key": "session-key-123"
}
```

**Status Response:**
```json
{
  "status": "running",
  "runtime_id": "runtime-123",
  "url": "http://localhost:8000",
  "work_hosts": {"host1": 8001},
  "session_api_key": "session-key-123",
  "sandbox_spec_id": "sandbox-spec-id"
}
```

## ID Mapping

The service maintains internal mappings between sandbox IDs (used by the app server) and runtime IDs (used by the remote runtime server). This allows the sandbox service to present a consistent interface while communicating with the legacy runtime protocol.

## Error Handling

- HTTP errors are converted to `SandboxError` exceptions
- Timeouts are handled gracefully with configurable timeout values
- 404 responses are handled appropriately (returning None for get operations, False for control operations)

## Limitations

- The `search_sandboxes` method is not implemented and returns empty results
- URL construction for exposed services uses a simplified pattern and may need customization for complex deployments
