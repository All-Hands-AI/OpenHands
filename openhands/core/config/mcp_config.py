import os
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

if TYPE_CHECKING:
    from openhands.core.config.openhands_config import OpenHandsConfig

from openhands.core.logger import openhands_logger as logger
from openhands.utils.import_utils import get_impl


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

    def __eq__(self, other):
        """Override equality operator to compare server configurations.

        Two server configurations are considered equal if they have the same
        name, command, args, and env values. The order of args is important,
        but the order of env variables is not.
        """
        if not isinstance(other, MCPStdioServerConfig):
            return False
        return (
            self.name == other.name
            and self.command == other.command
            and self.args == other.args
            and set(self.env.items()) == set(other.env.items())
        )


class MCPSHTTPServerConfig(BaseModel):
    url: str
    api_key: str | None = None


class MCPConfig(BaseModel):
    """Configuration for MCP (Message Control Protocol) settings.

    Attributes:
        sse_servers: List of MCP SSE server configs
        stdio_servers: List of MCP stdio server configs. These servers will be added to the MCP Router running inside runtime container.
    """

    sse_servers: list[MCPSSEServerConfig] = Field(default_factory=list)
    stdio_servers: list[MCPStdioServerConfig] = Field(default_factory=list)
    shttp_servers: list[MCPSHTTPServerConfig] = Field(default_factory=list)

    model_config = ConfigDict(extra='forbid')

    @staticmethod
    def _normalize_servers(servers_data: list[dict | str]) -> list[dict]:
        """Helper method to normalize SSE server configurations."""
        normalized = []
        for server in servers_data:
            if isinstance(server, str):
                normalized.append({'url': server})
            else:
                normalized.append(server)
        return normalized

    @model_validator(mode='before')
    def convert_string_urls(cls, data):
        """Convert string URLs to MCPSSEServerConfig objects."""
        if isinstance(data, dict):
            if 'sse_servers' in data:
                data['sse_servers'] = cls._normalize_servers(data['sse_servers'])

            if 'shttp_servers' in data:
                data['shttp_servers'] = cls._normalize_servers(data['shttp_servers'])

        return data

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
                data['sse_servers'] = cls._normalize_servers(data['sse_servers'])
                servers: list[
                    MCPSSEServerConfig | MCPStdioServerConfig | MCPSHTTPServerConfig
                ] = []
                for server in data['sse_servers']:
                    servers.append(MCPSSEServerConfig(**server))
                data['sse_servers'] = servers

            # Convert all entries in stdio_servers to MCPStdioServerConfig objects
            if 'stdio_servers' in data:
                servers = []
                for server in data['stdio_servers']:
                    servers.append(MCPStdioServerConfig(**server))
                data['stdio_servers'] = servers

            if 'shttp_servers' in data:
                data['shttp_servers'] = cls._normalize_servers(data['shttp_servers'])
                servers = []
                for server in data['shttp_servers']:
                    servers.append(MCPSHTTPServerConfig(**server))
                data['shttp_servers'] = servers

            # Create SSE config if present
            mcp_config = MCPConfig.model_validate(data)
            mcp_config.validate_servers()

            # Create the main MCP config
            mcp_mapping['mcp'] = cls(
                sse_servers=mcp_config.sse_servers,
                stdio_servers=mcp_config.stdio_servers,
                shttp_servers=mcp_config.shttp_servers,
            )
        except ValidationError as e:
            raise ValueError(f'Invalid MCP configuration: {e}')
        return mcp_mapping


class OpenHandsMCPConfig:
    @staticmethod
    def add_search_engine(app_config: 'OpenHandsConfig') -> MCPStdioServerConfig | None:
        """Add search engine to the MCP config"""
        if (
            app_config.search_api_key
            and app_config.search_api_key.get_secret_value().startswith('tvly-')
        ):
            logger.info('Adding search engine to MCP config')
            return MCPStdioServerConfig(
                name='tavily',
                command='npx',
                args=['-y', 'tavily-mcp@0.2.1'],
                env={'TAVILY_API_KEY': app_config.search_api_key.get_secret_value()},
            )
        else:
            logger.warning('No search engine API key found, skipping search engine')
        # Do not add search engine to MCP config in SaaS mode since it will be added by the OpenHands server
        return None

    @staticmethod
    def create_default_mcp_server_config(
        host: str, config: 'OpenHandsConfig', user_id: str | None = None
    ) -> tuple[MCPSHTTPServerConfig, list[MCPStdioServerConfig]]:
        """
        Create a default MCP server configuration.

        Args:
            host: Host string
            config: OpenHandsConfig
        Returns:
            tuple[MCPSSEServerConfig, list[MCPStdioServerConfig]]: A tuple containing the default SSE server configuration and a list of MCP stdio server configurations
        """
        stdio_servers = []
        search_engine_stdio_server = OpenHandsMCPConfig.add_search_engine(config)
        if search_engine_stdio_server:
            stdio_servers.append(search_engine_stdio_server)

        shttp_servers = MCPSHTTPServerConfig(url=f'http://{host}/mcp/mcp', api_key=None)
        return shttp_servers, stdio_servers


openhands_mcp_config_cls = os.environ.get(
    'OPENHANDS_MCP_CONFIG_CLS',
    'openhands.core.config.mcp_config.OpenHandsMCPConfig',
)

OpenHandsMCPConfigImpl = get_impl(OpenHandsMCPConfig, openhands_mcp_config_cls)
