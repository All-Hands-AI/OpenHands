from openhands_cli.user_actions.mcp_action import display_mcp_info


class MCPScreen:
    def __init__(self):
        pass

    def mcp_action_menu(self):
        """Display MCP configuration information directly."""
        try:
            display_mcp_info()
        except KeyboardInterrupt:
            return
