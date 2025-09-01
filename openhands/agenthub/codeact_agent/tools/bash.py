from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.agenthub.codeact_agent.tools.prompt import refine_prompt
from openhands.agenthub.codeact_agent.tools.security_utils import (
    RISK_LEVELS,
    SECURITY_RISK_DESC,
)
from openhands.llm.tool_names import EXECUTE_BASH_TOOL_NAME

_DETAILED_BASH_DESCRIPTION = """This tool runs bash commands in a persistent shell session. Your current directory, environment variables, and virtual environments are maintained across all commands.

## Execution Guidelines

* **Multiple Commands**: You can run a single command or chain multiple commands together using operators like `&&` and `;`.
* **Output Truncation**: If a command produces a large amount of output, the result may be truncated.
* **Working Directory**: For best results, **use absolute paths** instead of `cd` with relative paths.

## Timeouts and Long-Running Commands

* **Soft Timeout**: Each command has a **10-second soft timeout**. If a command exceeds this, you'll be prompted to let it continue or to interrupt it.
* **Long Tasks**: For commands that are expected to run for a long time (e.g., running a test suite), specify the expected duration in the `timeout` parameter to avoid the soft timeout prompt.
* **Background Processes**: To run a command indefinitely (like a web server), start it in the background and redirect its output. For example: `python3 app.py > server.log 2>&1 &`.

## Interacting with Long-Running Commands

If a command hits the 10-second soft timeout, you can continue to interact with the running process:

* **Get Latest Logs**: Send an empty command.
* **Send Input**: Pass text directly to the process's standard input (STDIN).
* **Send Control Signals**: Send control characters to interrupt or manage the process, such as `C-c` (Ctrl+C), `C-d` (Ctrl+D), or `C-z` (Ctrl+Z).
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
