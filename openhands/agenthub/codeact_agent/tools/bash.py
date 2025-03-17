from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_BASH_DESCRIPTION = """Execute a bash command in a persistent shell session.

### Command Execution
* One command at a time (chain with && or ; if needed)
* Persistent session: Environment variables and working directory persist between commands
* Timeout: 120 seconds, after which you can continue or interrupt

### Processes
* Long-running commands: For commands that may run indefinitely, run them in the background with redirection (example: python3 app.py > server.log 2>&1 &)
* For running processes (exit code -1), set is_input=true to:
  - Get more logs (send empty command)
  - Send text to STDIN (set command to text)
  - Send control signals (C-c, C-d, C-z)

### Best Practices
* Verify directories before creating files/directories
* Use absolute paths when possible
* Avoid excessive use of cd commands

### Output
* Long outputs will be truncated
"""

CmdRunTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='execute_bash',
        description=_BASH_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'The bash command to execute. Can be empty string to view additional logs when previous exit code is `-1`. Can be `C-c` (Ctrl+C) to interrupt the currently running process. Note: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.',
                },
                'is_input': {
                    'type': 'string',
                    'description': 'If True, the command is an input to the running process. If False, the command is a bash command to be executed in the terminal. Default is False.',
                    'enum': ['true', 'false'],
                },
            },
            'required': ['command'],
        },
    ),
)
