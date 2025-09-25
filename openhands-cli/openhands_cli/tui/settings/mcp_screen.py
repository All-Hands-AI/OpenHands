from pathlib import Path
from openhands_cli.locations import MCP_CONFIG_FILE, PERSISTENCE_DIR
from openhands_cli.tui.settings.store import AgentStore
from prompt_toolkit import HTML, print_formatted_text

from fastmcp.mcp_config import MCPConfig
from openhands.sdk import Agent


#    # File doesn't exist, that's okay - return empty config
#             return {}
#         except ValueError as e:
#             print_formatted_text(HTML(f"\n<red>Error loading MCP servers from ~/.openhands/{MCP_CONFIG_FILE}: {e}!</red>"))
#             return {}
#         except Exception as e:
#             print_formatted_text(HTML(f"\n<red>Unexpected error loading MCP configuration from ~/.openhands/{MCP_CONFIG_FILE}: {e}!</red>"))
#             return {}


class MCPScreen:
    """
    MCP Screen

    1. Display information about setting up MCP
    2. See existing servers that are setup
    3. Debug supplementary mcp config json file passed by user
    4. Display new servers which will be added on session restart

    """
    def __init__(self):
        self.store = AgentStore()


    def get_mcp_server_diff(self):
        pass



    def check_mcp_config_status(self):
        """Check the status of the MCP configuration file and return information about it."""
        config_path = Path(PERSISTENCE_DIR) / MCP_CONFIG_FILE

        if not config_path.exists():
            return {
                'exists': False,
                'valid': False,
                'servers': {},
                'message': f"MCP configuration file not found at ~/.openhands/{MCP_CONFIG_FILE}"
            }

        try:
            mcp_config = MCPConfig.from_file(config_path)
            servers = mcp_config.to_dict().get('mcpServers', {})
            return {
                'exists': True,
                'valid': True,
                'servers': servers,
                'message': f"Valid MCP configuration found with {len(servers)} server(s)"
            }
        except Exception as e:
            return {
                'exists': True,
                'valid': False,
                'servers': {},
                'message': f"Invalid MCP configuration file: {str(e)}"
            }


    def display_mcp_info(self, existing_agent: Agent):
        """Display comprehensive MCP configuration information."""
        print_formatted_text(HTML("<gold>MCP (Model Context Protocol) Configuration</gold>"))
        print_formatted_text("")

        # Display configuration format information
        print_formatted_text(HTML("<white>Configuration Format:</white>"))
        print_formatted_text(HTML("  The expected configuration format comes from:"))
        print_formatted_text(HTML("  <cyan>https://gofastmcp.com/clients/client#configuration-format</cyan>"))
        print_formatted_text("")

        # Display file location information
        print_formatted_text(HTML("<white>Configuration File Location:</white>"))
        print_formatted_text(HTML(f"  <cyan>~/.openhands/{MCP_CONFIG_FILE}</cyan>"))
        print_formatted_text("")

        # Check current configuration status
        status = self.check_mcp_config_status()

        if not status['exists']:
            print_formatted_text(HTML("<yellow>Status: Configuration file not found</yellow>"))
            print_formatted_text("")
            print_formatted_text(HTML("<white>To get started:</white>"))
            print_formatted_text(HTML("  1. Create the directory: <cyan>mkdir -p ~/.openhands</cyan>"))
            print_formatted_text(HTML("  2. Create the configuration file: <cyan>~/.openhands/mcp.json</cyan>"))
            print_formatted_text(HTML("  3. Add your MCP server configurations"))
            print_formatted_text(HTML("  4. Restart your OpenHands session to load the new configuration"))
        elif not status['valid']:
            print_formatted_text(HTML(f"<red>Status: {status['message']}</red>"))
            print_formatted_text("")
            print_formatted_text(HTML("<white>Please check your configuration file format.</white>"))
        else:
            print_formatted_text(HTML(f"<green>Status: {status['message']}</green>"))
            print_formatted_text("")

            if status['servers']:
                print_formatted_text(HTML("<white>Configured MCP Servers:</white>"))
                for name, config in status['servers'].items():
                    print_formatted_text(HTML(f"  <white>• {name}</white>"))

                    if 'command' in config:
                        command = config['command']
                        args = config.get('args', [])
                        args_str = ' '.join(args) if args else ''
                        print_formatted_text(HTML(f"    <grey>Type: Command-based</grey>"))
                        print_formatted_text(HTML(f"    <grey>Command: {command} {args_str}</grey>"))
                    elif 'url' in config:
                        url = config['url']
                        auth = config.get('auth', 'none')
                        print_formatted_text(HTML(f"    <grey>Type: URL-based</grey>"))
                        print_formatted_text(HTML(f"    <grey>URL: {url}</grey>"))
                        print_formatted_text(HTML(f"    <grey>Auth: {auth}</grey>"))
                    print_formatted_text("")
            else:
                print_formatted_text(HTML("<yellow>No MCP servers configured in the file.</yellow>"))

        print_formatted_text("")
        print_formatted_text(HTML("<white>Important Notes:</white>"))
        print_formatted_text(HTML("  • Changes to the configuration file will only take effect after restarting your session"))
        print_formatted_text(HTML("  • Make sure the configuration file follows the expected JSON format"))
        print_formatted_text(HTML("  • Server configurations will be merged with any existing agent MCP settings"))
        print_formatted_text("")
