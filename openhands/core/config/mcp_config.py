from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel, Field, ValidationError


class MCPConfig(BaseModel):
    """Configuration for MCP (Message Control Protocol) settings.

    Attributes:
        mcp_servers: List of MCP SSE (Server-Sent Events) server URLs.
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
            mcp_config = MCPConfig.model_validate(data)
            mcp_config.validate_servers()
            # Create the main MCP config
            mcp_mapping['mcp'] = cls(mcp_servers=mcp_config.mcp_servers)
        except ValidationError as e:
            raise ValueError(f'Invalid MCP configuration: {e}')

        return mcp_mapping
