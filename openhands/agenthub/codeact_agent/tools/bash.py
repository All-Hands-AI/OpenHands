import sys

from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import EXECUTE_BASH_TOOL_NAME

_DETAILED_BASH_DESCRIPTION = """Execute a bash command in the terminal within a persistent shell session.


### Command Execution
* One command at a time: You can only execute one bash command at a time. If you need to run multiple commands sequentially, use `&&` or `;` to chain them together.
* Persistent session: Commands execute in a persistent shell session where environment variables, virtual environments, and working directory persist between commands.
* Soft timeout: Commands have a soft timeout of 10 seconds, once that's reached, you have the option to continue or interrupt the command (see section below for details)

### Long-running Commands
* For commands that may run indefinitely, run them in the background and redirect output to a file, e.g. `python3 app.py > server.log 2>&1 &`.
* For commands that may run for a long time (e.g. installation or testing commands), or commands that run for a fixed amount of time (e.g. sleep), you should set the "timeout" parameter of your function call to an appropriate value.
* If a bash command returns exit code `-1`, this means the process hit the soft timeout and is not yet finished. By setting `is_input` to `true`, you can:
  - Send empty `command` to retrieve additional logs
  - Send text (set `command` to the text) to STDIN of the running process
  - Send control commands like `C-c` (Ctrl+C), `C-d` (Ctrl+D), or `C-z` (Ctrl+Z) to interrupt the process
  - If you do C-c, you can re-start the process with a longer "timeout" parameter to let it run to completion

### Terminal Recovery
* If the terminal becomes unresponsive or stuck, you can set `reset_terminal` to `true` to completely reset the terminal session.
* This will terminate all running processes and create a fresh terminal session.
* Note that this will lose all environment variables, working directory changes, and other session state.

### Best Practices
* Directory verification: Before creating new directories or files, first verify the parent directory exists and is the correct location.
* Directory management: Try to maintain working directory by using absolute paths and avoiding excessive use of `cd`.

### Output Handling
* Output truncation: If the output exceeds a maximum length, it will be truncated before being returned.
"""

_SHORT_BASH_DESCRIPTION = """Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, run in background and redirect output to a file, e.g. `python3 app.py > server.log 2>&1 &`. Use "timeout" parameter for commands with specific duration.
* Interact with running process: If exit code is `-1`, process is still running. Set `is_input` to `true` to send input, retrieve logs (empty `command`), or send control commands like `C-c`.
* One command at a time: Chain multiple commands with `&&` or `;`.
* Reset terminal: If terminal becomes unresponsive, set `reset_terminal` to `true` (loses session state)."""


def refine_prompt(prompt: str):
    if sys.platform == 'win32':
        return prompt.replace('bash', 'powershell')
    return prompt


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
                    'reset_terminal': {
                        'type': 'string',
                        'description': 'If True, completely resets the terminal session, terminating all running processes and creating a fresh session. This will lose all environment variables, working directory changes, and other session state. Default is False.',
                        'enum': ['true', 'false'],
                    },
                },
                'required': ['command'],
            },
        ),
    )
