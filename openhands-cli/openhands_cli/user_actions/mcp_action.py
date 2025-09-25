import enum
import os
from openhands_cli.user_actions.utils import (
    cli_confirm,
    cli_text_input,
)
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.validation import Validator, ValidationError



class MCPActionType(enum.Enum):
    LIST = 'list'
    ADD_JSON_CONFIG = 'add_json_config'


def load_mcp_config(config_path):
    import json

    with open(config_path, 'r') as f:
        mcp_config = json.load(f)

    return mcp_config




class MCPConfigValidator(Validator):
    def validate(self, document):
        path = document.text
        if not path:
            raise ValidationError(
                message="API key cannot be empty. Please entry valid file path"
            )

        if not os.path.isfile(path):
            raise ValidationError(
                message="Path either doesn't exist or is not a file"
            )

        mcp_config = None
        try:
            mcp_config = load_mcp_config()
        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Error decoding JSON from {path}: {e}"
            )
        except Exception as e:
            raise ValidationError(
                message=f"An unexpected error occurred while loading configuration: {e}"
            )

        from fastmcp.mcp_config import MCPConfig
        try:
            MCPConfig.model_validate(mcp_config)
        except Exception as e:
            raise ValidationError(
                message=f"Unable to load MCP config: {e}"
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

