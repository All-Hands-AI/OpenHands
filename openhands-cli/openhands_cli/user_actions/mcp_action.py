import enum
from openhands_cli.user_actions.utils import (
    cli_confirm,
    cli_text_input,
)
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.validation import Validator, ValidationError
from fastmcp.mcp_config import MCPConfig
from pathlib import Path


class MCPActionType(enum.Enum):
    LIST = 'list'
    ADD_JSON_CONFIG = 'add_json_config'


class MCPConfigValidator(Validator):
    def validate(self, document):
        path = document.text
        if not path:
            raise ValidationError(
                message="Path for MCP config cannot be empty. Please enter a valid path"
            )

        try:
            MCPConfig.from_file(Path(path))
        except ValueError as e:
            raise ValidationError(
                message=str(e)
            )
        except Exception as e:
            raise ValidationError(
                message=f"Error loading configuration: {e}"
            )


def mcp_action_menu() -> MCPActionType:
    """Display the main MCP configuration menu."""
    question = 'MCP Server Configuration - What would you like to do?'
    choices = [
        'List existing MCP servers',
        'Add MCP JSON config file',
        'Go back',
    ]

    index = cli_confirm(question, choices, escapable=True)

    action_map = {
        0: MCPActionType.LIST,
        1: MCPActionType.ADD_JSON_CONFIG,
    }

    if choices[index] == 'Go back':
        raise KeyboardInterrupt

    return action_map[index]



def propmt_mcp_json_config_file() -> str:
    question = 'Enter absolute path to MCP JSON config file (CTRL-c to cancel): '
    config_path = cli_text_input(
        question,
        escapable=True,
        validator=MCPConfigValidator()
    )
    return config_path

