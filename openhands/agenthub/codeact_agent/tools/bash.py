from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.agenthub.codeact_agent.tools.prompt import refine_prompt
from openhands.agenthub.codeact_agent.tools.security_utils import (
    RISK_LEVELS,
    SECURITY_RISK_DESC,
)
from openhands.llm.tool_names import EXECUTE_BASH_TOOL_NAME

_DETAILED_BASH_DESCRIPTION = """Execute a bash command in the terminal within a persistent shell session.

# Command Execution
- You can execute one  bash command at a time or use operators `&&` or `;` to execute multiple commands sequentially.
- Commands execute in a persistent shell session where environment variables, virtual environments, and working directory persist between commands.
- Soft timeout: all commands have a soft timeout of 10 seconds, once that's reached, after which you have an option to continue or interrupt the command.

# Long-running Commands
- Start all commands that are expected to run indefinitely in the background and redirect their output to a file, e.g. `python3 app.py > server.log 2>&1 &`.
- When running commands that are expected to run for a long time (e.g. automated tests or the `sleep` command) pass the expected run time in the `timeout` parameter.
- If a bash command returns exit code `-1`, this means that the process hit the soft timeout and is not yet finished. You can use the execute_bash tools to interact with such commands by setting the `is_input` parameter  to `true`. For example:
  - You can send an empty `command` to retrieve the latest logs.
  - You can send STDIN input to the running command by passing text in the `command` parameter.
  - You can send control commands like `C-c` (Ctrl+C), `C-d` (Ctrl+D), or `C-z` (Ctrl+Z) to interrupt the running command.

# Current directory
- Passing absolute paths to specify the working directory is preferred over using the `cd` command and relative paths.

# Command Output length
- If some command generates a large amount of output text it can be truncated.
"""

_SHORT_BASH_DESCRIPTION = """Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`. For commands that need to run for a specific duration, you can set the "timeout" argument to specify a hard timeout in seconds.
* Interact with running process: If a bash command returns exit code `-1`, this means the process is not yet finished. By setting `is_input` to `true`, the assistant can interact with the running process and send empty `command` to retrieve any additional logs, or send additional text (set `command` to the text) to STDIN of the running process, or send command like `C-c` (Ctrl+C), `C-d` (Ctrl+D), `C-z` (Ctrl+Z) to interrupt the process.
* One command at a time: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together."""


def create_cmd_run_tool(
    use_short_description: bool = False,
) -> ChatCompletionToolParam:
    description = (
        _SHORT_BASH_DESCRIPTION if use_short_description else _DETAILED_BASH_DESCRIPTION
    )
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=EXECUTE_BASH_TOOL_NAME,
            description=refine_prompt(description),
            parameters={
                'type': 'object',
                'properties': {
                    'command': {
                        'type': 'string',
                        'description': refine_prompt(
                            'The bash command to execute. Can be empty string to view additional logs when previous exit code is `-1`. Can be `C-c` (Ctrl+C) to interrupt the currently running process. Note: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.'
                        ),
                    },
                    'is_input': {
                        'type': 'string',
                        'description': refine_prompt(
                            'If True, the command is an input to the running process. If False, the command is a bash command to be executed in the terminal. Default is False.'
                        ),
                        'enum': ['true', 'false'],
                    },
                    'timeout': {
                        'type': 'number',
                        'description': 'Optional. Sets a hard timeout in seconds for the command execution. If not provided, the command will use the default soft timeout behavior.',
                    },
                    # 'security_risk': {
                    #     'type': 'string',
                    #     'description': SECURITY_RISK_DESC,
                    #     'enum': RISK_LEVELS,
                    # },
                },
                'required': ['command'],
            },
        ),
    )
