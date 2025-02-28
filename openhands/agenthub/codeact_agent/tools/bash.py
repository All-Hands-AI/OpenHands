from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_BASH_DESCRIPTION = """Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.
* Interact with running process: If a bash command returns exit code `-1`, this means the process is not yet finished. By setting `is_input` to `true`, the assistant can interact with the running process and send empty `command` to retrieve any additional logs, or send additional text (set `command` to the text) to STDIN of the running process, or send command like `C-c` (Ctrl+C), `C-d` (Ctrl+D), `C-z` (Ctrl+Z) to interrupt the process.
* One command at a time: You can only execute one bash command at a time. If you need to run multiple commands sequentially, you can use `&&` or `;` to chain them together.
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
