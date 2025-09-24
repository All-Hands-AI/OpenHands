import enum
from typing import Dict, Any, List, Optional

from openhands_cli.tui.utils import StepCounter
from openhands_cli.user_actions.utils import cli_confirm, cli_text_input
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


class NonEmptyValueValidator(Validator):
    def validate(self, document):
        text = document.text
        if not text:
            raise ValidationError(
                message="Value cannot be empty. Please enter a valid value."
            )


class MCPActionType(enum.Enum):
    LIST = 'list'
    ADD = 'add'
    REMOVE = 'remove'
    GO_BACK = 'go_back'


class MCPServerType(enum.Enum):
    COMMAND = 'command'
    URL = 'url'


# In-memory storage for MCP servers (for now, as requested)
_mcp_servers: Dict[str, Dict[str, Any]] = {}


def mcp_action_menu() -> MCPActionType:
    """Display the main MCP configuration menu."""
    question = 'MCP Server Configuration - What would you like to do?'
    choices = [
        'List existing MCP servers',
        'Add a new MCP server',
        'Remove an MCP server',
        'Go back',
    ]

    index = cli_confirm(question, choices, escapable=True)

    action_map = {
        0: MCPActionType.LIST,
        1: MCPActionType.ADD,
        2: MCPActionType.REMOVE,
        3: MCPActionType.GO_BACK
    }

    return action_map[index]


def list_mcp_servers() -> None:
    """Display all configured MCP servers."""
    if not _mcp_servers:
        print_formatted_text(HTML("<yellow>No MCP servers configured.</yellow>"))
        return

    print_formatted_text(HTML("<gold>Configured MCP Servers:</gold>"))
    print_formatted_text("")
    
    for name, config in _mcp_servers.items():
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


def choose_server_type(step_counter: StepCounter) -> MCPServerType:
    """Choose the type of MCP server to add."""
    question = step_counter.next_step('Select MCP Server Type:')
    choices = [
        'Command-based server (e.g., fetch, repomix)',
        'URL-based server (e.g., Notion with OAuth)',
    ]

    index = cli_confirm(question, choices, escapable=True)
    
    return MCPServerType.COMMAND if index == 0 else MCPServerType.URL


def prompt_server_name(step_counter: StepCounter, existing_names: List[str]) -> str:
    """Prompt for MCP server name with validation."""
    while True:
        question = step_counter.next_step('Enter server name (CTRL-c to cancel): ')
        name = cli_text_input(question, escapable=True, validator=NonEmptyValueValidator())
        
        if name in existing_names:
            print_formatted_text(HTML(f"<red>Server '{name}' already exists. Please choose a different name.</red>"))
            continue
        
        return name


def prompt_command_config(step_counter: StepCounter) -> Dict[str, Any]:
    """Prompt for command-based server configuration."""
    command = cli_text_input(
        step_counter.next_step('Enter command (e.g., uvx, npx): '),
        escapable=True,
        validator=NonEmptyValueValidator()
    )
    
    args_input = cli_text_input(
        step_counter.next_step('Enter arguments (space-separated, or press ENTER for none): '),
        escapable=True
    )
    
    config = {'command': command}
    if args_input.strip():
        config['args'] = args_input.strip().split()
    
    return config


def prompt_url_config(step_counter: StepCounter) -> Dict[str, Any]:
    """Prompt for URL-based server configuration."""
    url = cli_text_input(
        step_counter.next_step('Enter server URL: '),
        escapable=True,
        validator=NonEmptyValueValidator()
    )
    
    question = step_counter.next_step('Select authentication type:')
    auth_choices = ['none', 'oauth', 'api_key']
    auth_index = cli_confirm(question, auth_choices, escapable=True)
    auth_type = auth_choices[auth_index]
    
    config = {'url': url}
    if auth_type != 'none':
        config['auth'] = auth_type
    
    return config


def add_mcp_server() -> None:
    """Add a new MCP server configuration."""
    step_counter = StepCounter()
    
    try:
        # Get server name
        server_name = prompt_server_name(step_counter, list(_mcp_servers.keys()))
        
        # Get server type
        server_type = choose_server_type(step_counter)
        
        # Get server configuration based on type
        if server_type == MCPServerType.COMMAND:
            config = prompt_command_config(step_counter)
        else:
            config = prompt_url_config(step_counter)
        
        # Store the configuration
        _mcp_servers[server_name] = config
        
        print_formatted_text(HTML(f"<green>✓ MCP server '{server_name}' added successfully!</green>"))
        
        # Display the configuration
        print_formatted_text(HTML("<grey>Configuration:</grey>"))
        for key, value in config.items():
            if isinstance(value, list):
                value = ' '.join(value)
            print_formatted_text(HTML(f"<grey>  {key}: {value}</grey>"))
        
    except KeyboardInterrupt:
        print_formatted_text(HTML("<yellow>Operation cancelled.</yellow>"))


def remove_mcp_server() -> None:
    """Remove an existing MCP server configuration."""
    if not _mcp_servers:
        print_formatted_text(HTML("<yellow>No MCP servers configured to remove.</yellow>"))
        return
    
    question = 'Select server to remove:'
    server_names = list(_mcp_servers.keys())
    choices = server_names + ['Cancel']
    
    try:
        index = cli_confirm(question, choices, escapable=True)
        
        if index == len(server_names):  # Cancel option
            print_formatted_text(HTML("<yellow>Operation cancelled.</yellow>"))
            return
        
        server_name = server_names[index]
        
        # Confirm removal
        confirm_question = f"Are you sure you want to remove server '{server_name}'?"
        confirm_choices = ['Yes, remove it', 'No, keep it']
        confirm_index = cli_confirm(confirm_question, confirm_choices, escapable=True)
        
        if confirm_index == 0:
            del _mcp_servers[server_name]
            print_formatted_text(HTML(f"<green>✓ MCP server '{server_name}' removed successfully!</green>"))
        else:
            print_formatted_text(HTML("<yellow>Operation cancelled.</yellow>"))
            
    except KeyboardInterrupt:
        print_formatted_text(HTML("<yellow>Operation cancelled.</yellow>"))


def handle_mcp_configuration() -> None:
    """Main handler for MCP configuration menu."""
    while True:
        try:
            action = mcp_action_menu()
            
            if action == MCPActionType.LIST:
                list_mcp_servers()
            elif action == MCPActionType.ADD:
                add_mcp_server()
            elif action == MCPActionType.REMOVE:
                remove_mcp_server()
            elif action == MCPActionType.GO_BACK:
                break
                
        except KeyboardInterrupt:
            print_formatted_text(HTML("<yellow>Returning to main menu...</yellow>"))
            break


def get_mcp_config() -> Dict[str, Any]:
    """Get the current MCP configuration in the format expected by the agent SDK."""
    if not _mcp_servers:
        return {}
    
    config = {"mcpServers": {}}
    for name, server_config in _mcp_servers.items():
        if 'command' in server_config:
            # Command-based server
            config["mcpServers"][name] = {
                "command": server_config['command'],
                "args": server_config.get('args', [])
            }
        elif 'url' in server_config:
            # URL-based server (OAuth)
            config["mcpServers"][name] = {
                "url": server_config['url']
            }
            if server_config.get('auth') == 'oauth':
                config["mcpServers"][name]["auth"] = "oauth"
    
    return config