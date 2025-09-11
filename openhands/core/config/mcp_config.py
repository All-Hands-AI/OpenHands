import os

from openhands_configuration import MCPSHTTPServerConfig, MCPStdioServerConfig


from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.utils.import_utils import get_impl
from openhands.core.logger import openhands_logger as logger

class OpenHandsMCPConfig:
    @staticmethod
    def add_search_engine(app_config: 'OpenHandsConfig') -> MCPStdioServerConfig | None:
        """Add search engine to the MCP config."""
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
    ) -> tuple[MCPSHTTPServerConfig | None, list[MCPStdioServerConfig]]:
        """Create a default MCP server configuration.
        Args:
            host: Host string
            config: OpenHandsConfig
            user_id: Optional user ID for the MCP server
        Returns:
            tuple[MCPSHTTPServerConfig | None, list[MCPStdioServerConfig]]: A tuple containing the default SHTTP server configuration (or None) and a list of MCP stdio server configurations
        """
        stdio_servers = []
        search_engine_stdio_server = OpenHandsMCPConfig.add_search_engine(config)
        if search_engine_stdio_server:
            stdio_servers.append(search_engine_stdio_server)

        shttp_servers = MCPSHTTPServerConfig(url=f'http://{host}/mcp/mcp', api_key=None)

        return shttp_servers, stdio_servers


openhands_mcp_config_cls = os.environ.get(
    'OPENHANDS_MCP_CONFIG_CLS',
    'opehands_configuration.OpenHandsMCPConfig',
)

OpenHandsMCPConfigImpl = get_impl(OpenHandsMCPConfig, openhands_mcp_config_cls)
