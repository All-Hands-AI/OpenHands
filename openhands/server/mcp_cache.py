import asyncio
from typing import Dict, List, Optional, Set

from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.search_engine import SearchEngineConfig
from openhands.core.logger import openhands_logger as logger
from openhands.mcp.client import MCPClient
from openhands.mcp.utils import fetch_search_tools_from_config


class MCPToolsCache:
    """Simple cache for MCP and Search tools"""

    def __init__(self):
        self.mcp_tools: dict[str, List[dict]] = {}
        self.search_tools: List[dict] = []
        self._is_loaded = False

    def _is_initialized(self) -> bool:
        """Check if tools are initialized"""
        return self._is_loaded

    async def fetch_mcp_tools(
        self,
        dict_mcp_config: Dict[str, MCPConfig],
        sid: Optional[str] = None,
        mnemonic: Optional[str] = None,
    ):
        async def connect_single_client(
            name: str, mcp_config: MCPConfig
        ) -> Optional[dict[str, List[dict]]]:
            """Connect to a single MCP server and return the client or None on failure."""
            logger.info(
                f'Initializing MCP {name} agent for {mcp_config.url} with {mcp_config.mode} connection...'
            )

            if f'search_engine_{name}' in dict_mcp_config:
                return None

            client = MCPClient(name=name)
            tools = []
            try:
                await client.connect_sse(mcp_config.url, sid, mnemonic)
                for tool in client.tools:
                    mcp_tools = tool.to_param()
                    tools.append(mcp_tools)
                # Always disconnect clients to clean up resources
                await client.disconnect()
                return {name: tools}
            except Exception as e:
                logger.error(f'Failed to connect to {mcp_config.url}: {str(e)}')
                return {name: []}

        connection_tasks = [
            connect_single_client(name, mcp_config)
            for name, mcp_config in dict_mcp_config.items()
        ]

        results = await asyncio.gather(*connection_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Unexpected error during MCP client connection: {result}')
            elif result is not None and isinstance(result, dict):
                self.mcp_tools.update(result)

    async def fetch_search_tools(
        self,
        dict_search_config: Dict[str, SearchEngineConfig],
        sid: Optional[str] = None,
        mnemonic: Optional[str] = None,
    ):
        self.search_tools = await fetch_search_tools_from_config(
            dict_search_config, sid, mnemonic
        )

    async def initialize_tools(
        self,
        dict_mcp_config: Dict[str, MCPConfig],
        dict_search_config: Dict[str, SearchEngineConfig],
        sid: Optional[str] = None,
        mnemonic: Optional[str] = None,
    ):
        """Initialize and load all tools"""
        if self._is_loaded:
            return

        logger.info('Loading MCP and Search tools...')
        await self.fetch_mcp_tools(dict_mcp_config, sid, mnemonic)
        await self.fetch_search_tools(dict_search_config, sid, mnemonic)
        self._is_loaded = True

    @property
    def is_loaded(self) -> bool:
        """Check if tools are loaded"""
        return self._is_loaded

    def get_flat_mcp_tools(
        self, disabled_mcp_names: Optional[Set[str]] = None
    ) -> List[dict]:
        """Get flat list of MCP tools"""
        if not disabled_mcp_names:
            return [tool for tools in self.mcp_tools.values() for tool in tools]
        else:
            res = []
            for name, tools in self.mcp_tools.items():
                if name not in disabled_mcp_names:
                    res.extend(tools)
            return res

    def get_search_tools(self) -> List[dict]:
        """Get search tools"""
        return self.search_tools


mcp_tools_cache = MCPToolsCache()
