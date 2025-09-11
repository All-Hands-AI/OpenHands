import os

from openhands_configuration import OpenHandsMCPConfig

from openhands.utils.import_utils import get_impl

openhands_mcp_config_cls = os.environ.get(
    'OPENHANDS_MCP_CONFIG_CLS',
    'opehands_configuration.OpenHandsMCPConfig',
)

OpenHandsMCPConfigImpl = get_impl(OpenHandsMCPConfig, openhands_mcp_config_cls)
