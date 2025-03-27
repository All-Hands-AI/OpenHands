from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError


class MCPSSEConfig(BaseModel):
    """Configuration for MCP SSE (Server-Sent Events) settings.

    Attributes:
        mcp_servers: List of MCP server URLs.
    """

    mcp_servers: List[str] = Field(default_factory=list)

    model_config = {'extra': 'forbid'}

    def validate_servers(self) -> None:
        """Validate that server URLs are valid and unique."""
        # Check for duplicate server URLs
        if len(set(self.mcp_servers)) != len(self.mcp_servers):
            raise ValueError('Duplicate MCP server URLs are not allowed')

        # Validate URLs
        for url in self.mcp_servers:
            try:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError(f'Invalid URL format: {url}')
            except Exception as e:
                raise ValueError(f'Invalid URL {url}: {str(e)}')


class MCPStdioConfig(BaseModel):
    """Configuration for MCP stdio settings.

    Attributes:
        commands: List of commands to run.
        args: List of arguments for each command.
    """

    commands: List[str] = Field(default_factory=list)
    args: List[List[str]] = Field(default_factory=list)

    model_config = {'extra': 'forbid'}

    def validate_stdio(self) -> None:
        """Validate that commands and args are properly configured."""

        # Check if number of commands matches number of args lists
        if len(self.commands) != len(self.args):
            raise ValueError(
                f'Number of commands ({len(self.commands)}) does not match '
                f'number of args lists ({len(self.args)})'
            )


class MCPConfig(BaseModel):
    """Configuration for MCP (Message Control Protocol) settings.

    Attributes:
        sse: SSE-specific configuration.
        stdio: stdio-specific configuration.
    """

    sse: MCPSSEConfig = Field(default_factory=MCPSSEConfig)
    stdio: MCPStdioConfig = Field(default_factory=MCPStdioConfig)

    model_config = {'extra': 'forbid'}

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'MCPConfig']:
        """
        Create a mapping of MCPConfig instances from a toml dictionary representing the [mcp] section.

        The configuration is built from all keys in data.

        Returns:
            dict[str, MCPConfig]: A mapping where the key "mcp" corresponds to the [mcp] configuration
        """
        # Initialize the result mapping
        mcp_mapping: dict[str, MCPConfig] = {}

        try:
            # Create SSE config if present
            sse_config = MCPSSEConfig(**data.get('mcp-sse', {}))
            sse_config.validate_servers()

            # Create stdio config if present
            stdio_config = MCPStdioConfig(**data.get('mcp-stdio', {}))
            stdio_config.validate_stdio()

            # Create the main MCP config
            mcp_mapping['mcp'] = cls(sse=sse_config, stdio=stdio_config)
        except ValidationError as e:
            raise ValueError(f'Invalid MCP configuration: {e}')

        return mcp_mapping
