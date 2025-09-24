from typing import Any
from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.tui.utils import StepCounter
from openhands_cli.user_actions.mcp_action import (
    MCPActionType,
    MCPServerType,
    choose_server_type,
    mcp_action_menu,
    prompt_command_config,
    prompt_server_name,
    prompt_url_config
)
from prompt_toolkit import HTML, print_formatted_text


class MCPScreen:
    def __init__(self):
        self.agent_store = AgentStore()


    def _list_mcp_servers(self) -> dict[str, Any]:
        agent = self.agent_store.load()
        if not agent:
            return

        return agent.mcp_config.get('mcpServers', {})


    def mcp_action_menu(self):
        try:
            settings_type = mcp_action_menu()
        except KeyboardInterrupt:
            return

        if settings_type == MCPActionType.LIST:
            self.list_mcp_servers()

        elif settings_type == MCPActionType.ADD:
            self.handle_add_mcp_server()

        elif settings_type == MCPActionType.REMOVE:
            self.handle_remove_mcp_server()


    def handle_add_mcp_server(self):
        step_counter = StepCounter(4)

        try:
            server_name = prompt_server_name(step_counter)
            server_type = choose_server_type(step_counter)
            if server_type == MCPServerType.STDIO:
                config = prompt_command_config(step_counter)
            else:
                config = prompt_url_config(step_counter)

            self.save_mcp_configuration(server_name, config)

        except Exception:
            print_formatted_text(HTML('\n<red>Cancelled settings change.</red>'))
            return


    def handle_remove_mcp_server(self):
        pass


    def save_mcp_configuration(
        self,
        server_name: str,
        server_config: dict[str, Any]
    ):
        agent = self.agent_store.load()
        if not agent:
            return

        mcp_config = agent.mcp_config.copy()
        if not mcp_config:
            mcp_config = {"mcpServers": {}}

        mcp_config["mcpServers"][server_name] = server_config

        agent = agent.model_copy(update={"mcp_config": mcp_config})
        self.agent_store.save(agent)

        print_formatted_text(HTML(f"<green>✓ MCP server '{server_name}' added successfully!</green>"))


        print_formatted_text(HTML("<grey>Configuration:</grey>"))
        for key, value in server_config.items():
            if isinstance(value, list):
                value = ' '.join(value)
            print_formatted_text(HTML(f"<grey>  {key}: {value}</grey>"))


    def list_mcp_servers(self) -> None:
        """Display all configured MCP servers."""

        mcp_servers = self._list_mcp_servers()
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
