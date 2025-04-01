"""
MCP (Model Context Protocol) integration for OpenHands
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP, Context
from openhands.core.config.loader import get_config  # Configuration loader

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[dict]:
    """MCP server lifespan management"""
    config = get_config()
    mcp = FastMCP("OpenHands")
    
    # Configure logging if enabled
    if config.mcp_logging:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("mcp")
        logger.info(f"Starting MCP server on port {config.mcp_port}")
    
    yield {"mcp": mcp, "config": config}

# Initialize configuration
config = get_config()
mcp = FastMCP("OpenHands")

# Core OpenHands resources
@mcp.resource("openhands://config")
def get_config_resource() -> str:
    """Expose OpenHands configuration"""
    return str(get_config())

@mcp.resource("openhands://codebase")
def get_codebase_info() -> dict:
    """Get codebase metadata"""
    return {
        "language": "Python",
        "version": "0.30.1",
        "main_package": "openhands",
        "dependencies": ["litellm", "pandas", "numpy"]
    }

@mcp.resource("openhands://task/current")
async def get_current_task() -> dict:
    """Get current task execution status"""
    ctx = mcp.get_current_context()
    return {
        "status": "active",
        "timestamp": ctx.request_time.isoformat(),
        "resources": await ctx.list_resources()
    }

@mcp.resource("openhands://repository")
def get_repository_info() -> dict:
    """Get repository metadata"""
    return {
        "name": "OpenHands",
        "description": "Automated AI software engineer",
        "components": ["backend", "frontend"]
    }

# Security configuration
ALLOWED_COMMANDS = {
    "git": ["clone", "pull", "status"],
    "ls": ["-l", "-a"],
    "cat": [],
    "python": ["-c"],
}

def validate_command(command: str) -> None:
    """Validate command against security policy"""
    parts = command.split()
    if not parts:
        raise ValueError("Empty command")
    
    base_cmd = parts[0]
    if base_cmd not in ALLOWED_COMMANDS:
        raise ValueError(f"Command not allowed: {base_cmd}")
    
    if len(parts) > 1:
        allowed_args = ALLOWED_COMMANDS[base_cmd]
        if allowed_args and parts[1] not in allowed_args:
            raise ValueError(f"Invalid arguments for {base_cmd}")

# Tool integration
@mcp.tool()
async def execute_command(command: str, ctx: Context) -> str:
    """Execute validated shell commands through OpenHands"""
    validate_command(command)
    return await ctx.run_command(command)

# Mount MCP to FastAPI
app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    if config.mcp_enabled:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.mcp_port,
            log_level="info" if config.mcp_logging else "warning",
            lifespan="on"
        )
    else:
        print("MCP server is disabled in configuration")