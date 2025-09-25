from typing import Any
from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.tui.utils import StepCounter
from openhands_cli.user_actions.mcp_action import (
    MCPActionType,
    load_mcp_config,
    mcp_action_menu,
    propmt_mcp_json_config_file
)
from prompt_toolkit import HTML, print_formatted_text


class MCPScreen:
    def __init__(self):
        self.agent_store = AgentStore()

    def mcp_action_menu(self):
        try:
            settings_type = mcp_action_menu()
        except KeyboardInterrupt:
            return

        if settings_type == MCPActionType.LIST:
            self.list_mcp_servers()

        if settings_type == MCPActionType.ADD_JSON_CONFIG:
            config_path = propmt_mcp_json_config_file()
            self.save_mcp_configuration(config_path)


    def save_mcp_configuration(
        self,
        config_path: str
    ):

        mcp_config = load_mcp_config(config_path)


        agent = self.agent_store.load()
        if not agent:
            return

        mcp_config = agent.mcp_config.copy()
        agent = agent.model_copy(update={"mcp_config": mcp_config})
        self.agent_store.save(agent)

        print_formatted_text(HTML(f"<green>✓ MCP config added successfully!</green>"))


    def list_mcp_servers(self) -> None:
        """Display all configured MCP servers."""

        agent = self.agent_store.load()
        if not agent:
            return

        mcp_servers = agent.mcp_config.get('mcpServers', {})

        if not mcp_servers:
            print_formatted_text(HTML("<yellow>No MCP servers configured.</yellow>"))
            return

        print_formatted_text(HTML("<gold>Configured MCP Servers:</gold>"))
        print_formatted_text("")

        for name, config in mcp_servers.items():
            print_formatted_text(HTML(f"<white>• {name}</white>"))

            if 'command' in config:
                command = config['command']
                args = config.get('args', [])
                args_str = ' '.join(args) if args else ''
                print_formatted_text(HTML(f"  <grey>Type: Command-based</grey>"))
                print_formatted_text(HTML(f"  <grey>Command: {command} {args_str}</grey>"))
            elif 'url' in config:
                url = config['url']
                auth = config.get('auth', 'none')
                print_formatted_text(HTML(f"  <grey>Type: URL-based</grey>"))
                print_formatted_text(HTML(f"  <grey>URL: {url}</grey>"))
                print_formatted_text(HTML(f"  <grey>Auth: {auth}</grey>"))

            print_formatted_text("")
