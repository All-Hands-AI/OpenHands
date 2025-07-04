import sys

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import EXECUTE_BASH_TOOL_NAME, EXECUTE_POWERSHELL_TOOL_NAME

_DETAILED_SHELL_DESCRIPTION_TEMPLATE = """Execute a {shell} command in the terminal within a persistent shell session.


### Command Execution
* One command at a time: You can only execute one {shell} command at a time. If you need to run multiple commands sequentially, use `&&` or `;` to chain them together.
* Persistent session: Commands execute in a persistent shell session where environment variables, virtual environments, and working directory persist between commands.
* Soft timeout: Commands have a soft timeout of 10 seconds, once that's reached, you have the option to continue or interrupt the command (see section below for details)

### Long-running Commands
* For commands that may run indefinitely, run them in the background and redirect output to a file, e.g. `python3 app.py > server.log 2>&1 &`.
* For commands that may run for a long time (e.g. installation or testing commands), or commands that run for a fixed amount of time (e.g. sleep), you should set the "timeout" parameter of your function call to an appropriate value.
* If a {shell} command returns exit code `-1`, this means the process hit the soft timeout and is not yet finished. By setting `is_input` to `true`, you can:
  - Send empty `command` to retrieve additional logs
  - Send text (set `command` to the text) to STDIN of the running process
  - Send control commands like `C-c` (Ctrl+C), `C-d` (Ctrl+D), or `C-z` (Ctrl+Z) to interrupt the process
  - If you do C-c, you can re-start the process with a longer "timeout" parameter to let it run to completion

### Best Practices
* Directory verification: Before creating new directories or files, first verify the parent directory exists and is the correct location.
* Directory management: Try to maintain working directory by using absolute paths and avoiding excessive use of `cd`.

### Output Handling
* Output truncation: If the output exceeds a maximum length, it will be truncated before being returned.
"""

_SHORT_SHELL_DESCRIPTION_TEMPLATE = """Execute a {shell} command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`. For commands that need to run for a specific duration, you can set the "timeout" argument to specify a hard timeout in seconds.
* Interact with running process: If a {shell} command returns exit code `-1`, this means the process is not yet finished. By setting `is_input` to `true`, the assistant can interact with the running process and send empty `command` to retrieve any additional logs, or send additional text (set `command` to the text) to STDIN of the running process, or send command like `C-c` (Ctrl+C), `C-d` (Ctrl+D), `C-z` (Ctrl+Z) to interrupt the process.
* One command at a time: You can only execute one {shell} command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together."""


def get_shell_type(shell_config: str | None = None) -> str:
    """Determine the shell type based on configuration or OS default."""
    if shell_config:
        return shell_config.lower()

    # Default based on OS
    if sys.platform == 'win32':
        return 'powershell'
    else:
        return 'bash'


def get_tool_name(shell_type: str) -> str:
    """Get the appropriate tool name for the shell type."""
    if shell_type == 'powershell':
        return EXECUTE_POWERSHELL_TOOL_NAME
    else:
        return EXECUTE_BASH_TOOL_NAME


def create_cmd_run_tool(
    use_short_description: bool = False,
    shell_config: str | None = None,
) -> ChatCompletionToolParam:
    """Create a command execution tool with the specified shell configuration."""
    shell_type = get_shell_type(shell_config)
    tool_name = get_tool_name(shell_type)

    description_template = (
        _SHORT_SHELL_DESCRIPTION_TEMPLATE if use_short_description else _DETAILED_SHELL_DESCRIPTION_TEMPLATE
    )
    description = description_template.format(shell=shell_type)

    command_description = f'The {shell_type} command to execute. Can be empty string to view additional logs when previous exit code is `-1`. Can be `C-c` (Ctrl+C) to interrupt the currently running process. Note: You can only execute one {shell_type} command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.'

    is_input_description = f'If True, the command is an input to the running process. If False, the command is a {shell_type} command to be executed in the terminal. Default is False.'

    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=tool_name,
            description=description,
            parameters={
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': command_description,
                    },
                    'is_input': {
                        'type': 'string',
                        'description': is_input_description,
                        'enum': ['true', 'false'],
                    },
                    'timeout': {
                        'type': 'number',
                        'description': 'Optional. Sets a hard timeout in seconds for the command execution. If not provided, the command will use the default soft timeout behavior.',
                    },
                },
                'required': ['command'],
            },
        ),
    )
