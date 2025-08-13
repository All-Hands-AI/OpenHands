# OpenHands Dependency Analysis

## Component Dependencies

### CLI Component
- `prompt_toolkit` - Interactive command-line interfaces
- Core: `jinja2`, `toml`, `pydantic`, `httpx`, standard library

### Server Component
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `python-multipart` - File upload support
- `tornado` - WebSocket support
- `python-socketio` - Socket.IO
- `sse-starlette` - Server-sent events
- Core: `httpx`, `jinja2`, `pathspec`, standard library

### Resolver Component
- Uses core functionality only: `httpx`, `jinja2`, `litellm`, `termcolor`

## Current Structure

### Core Dependencies (Always Installed)
- `litellm` - LLM API integration
- `aiohttp` - Async HTTP client/server
- `httpx` - Modern HTTP client (via httpx-aiohttp)
- `fastmcp` - Model Context Protocol
- `pydantic` - Data validation
- `jinja2` - Template rendering
- `pyyaml` - YAML parsing
- `toml` - TOML configuration
- `bashlex` - Bash parsing
- `psutil` - System monitoring
- `pexpect` - Process interaction
- `termcolor` - Terminal colors

### Optional Dependencies
```toml
[tool.poetry.extras]
cli = ["prompt-toolkit"]
server = ["fastapi", "uvicorn", "python-multipart", "tornado", "python-socketio", "sse-starlette"]
resolver = []  # Uses core functionality only

[tool.poetry.group.ci.dependencies]
# CI convenience group - includes all extras as regular dependencies
prompt-toolkit = "*"
fastapi = "*"
uvicorn = "*"
python-multipart = "*"
tornado = "*"
python-socketio = "*"
sse-starlette = "*"
```

## Heavy Dependencies (Made Optional)
- `docker` - Container management
- `kubernetes` - Kubernetes integration
- `boto3` - AWS services
- `browsergym-core` - Browser environments
- `PyPDF2`, `python-docx`, `python-pptx` - File processing
- `numpy`, `memory-profiler` - Performance tools

## Usage
- End users: `pip install openhands-ai[cli,server]`
- CI/Development: `poetry install --with ci`
- Core only: `pip install openhands-ai`
