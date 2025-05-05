from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError


class MCPSSEServerConfig(BaseModel):
    """Configuration for a single MCP server.

    Attributes:
        url: The server URL
        api_key: Optional API key for authentication
    """

    url: str
    api_key: str | None = None


class MCPStdioServerConfig(BaseModel):
    """Configuration for a MCP server that uses stdio.

    Attributes:
        name: The name of the server
        command: The command to run the server
        args: The arguments to pass to the server
        env: The environment variables to set for the server
    """

    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class MCPConfig(BaseModel):
    """Configuration for MCP (Message Control Protocol) settings.

    Attributes:
        sse_servers: List of MCP SSE server configs
        stdio_servers: List of MCP stdio server configs. These servers will be added to the MCP Router running inside runtime container.
    """

    sse_servers: list[MCPSSEServerConfig] = Field(default_factory=list)
    stdio_servers: list[MCPStdioServerConfig] = Field(default_factory=list)

    model_config = {'extra': 'forbid'}

    def validate_servers(self) -> None:
        """Validate that server URLs are valid and unique."""
        urls = [server.url for server in self.sse_servers]

        # Check for duplicate server URLs
        if len(set(urls)) != len(urls):
            raise ValueError('Duplicate MCP server URLs are not allowed')

        # Validate URLs
        for url in urls:
            try:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError(f'Invalid URL format: {url}')
            except Exception as e:
                raise ValueError(f'Invalid URL {url}: {str(e)}')

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
            # Convert all entries in sse_servers to MCPSSEServerConfig objects
            if 'sse_servers' in data:
                servers = []
                for server in data['sse_servers']:
                    if isinstance(server, dict):
                        servers.append(MCPSSEServerConfig(**server))
                    else:
                        # Convert string URLs to MCPSSEServerConfig objects with no API key
                        servers.append(MCPSSEServerConfig(url=server))
                data['sse_servers'] = servers

            # Convert all entries in stdio_servers to MCPStdioServerConfig objects
            if 'stdio_servers' in data:
                servers = []
                for server in data['stdio_servers']:
                    servers.append(MCPStdioServerConfig(**server))
                data['stdio_servers'] = servers

            # Create SSE config if present
            mcp_config = MCPConfig.model_validate(data)
            mcp_config.validate_servers()
            # Create the main MCP config
            mcp_mapping['mcp'] = cls(
                sse_servers=mcp_config.sse_servers,
                stdio_servers=mcp_config.stdio_servers,
            )
        except ValidationError as e:
            raise ValueError(f'Invalid MCP configuration: {e}')

        return mcp_mapping
