from openhands_cli.user_actions.mcp_action import mcp_action_menu


class MCPScreen:
    def mcp_action_menu(self):
        try:
            settings_type = mcp_action_menu()
        except KeyboardInterrupt:
            return
