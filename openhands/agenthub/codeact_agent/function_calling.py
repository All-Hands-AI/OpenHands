"""This file contains the function calling implementation for different actions.

This is similar to the functionality of `CodeActResponseParser`.
"""

import json

from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    Action,
    AgentDelegateAction,
    AgentFinishAction,
    CmdRunAction,
    IPythonRunCellAction,
    MessageAction,
)
from openhands.runtime.plugins import AgentSkillsRequirement

_BASH_DESCRIPTION = """Execute a bash command in the terminal.
* Long running commands: For commands that may run indefinitely, it should be run in the background and the output should be redirected to a file, e.g. command = `python3 app.py > server.log 2>&1 &`.
* Interactive: If a bash command returns exit code `-1`, this means the process is not yet finished. The assistant must then send a second call to terminal with an empty `command` (which will retrieve any additional logs), or it can send additional text (set `command` to the text) to STDIN of the running process, or it can send command=`ctrl+c` to interrupt the process.
* Timeout: If a command execution result says "Command timed out. Sending SIGINT to the process", the assistant should retry running the command in the background.
"""

CmdRunTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='execute_bash',
        description=_BASH_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'thought': {
                    'type': 'string',
                    'description': 'Reasoning about the action to take.',
                },
                'command': {
                    'type': 'string',
                    'description': 'The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.',
                },
            },
            'required': ['command'],
        },
    ),
)

_IPYTHON_DESCRIPTION = f"""Run a cell of Python code in an IPython environment.
* The assistant should define variables and import packages before using them.
* The variable defined in the IPython environment will not be available outside the IPython environment (e.g., in terminal).
* Apart from the standard Python library, the assistant can also use the following functions (already imported):
{AgentSkillsRequirement.documentation}
"""

IPythonTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='execute_ipython_cell',
        description=_IPYTHON_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'thought': {
                    'type': 'string',
                    'description': 'Reasoning about the action to take.',
                },
                'code': {
                    'type': 'string',
                    'description': 'The Python code to execute. Supports magic commands like %pip.',
                },
            },
            'required': ['code'],
        },
    ),
)

_FILE_EDIT_DESCRIPTION = """Edit a file.
* The assistant can edit files by specifying the file path and providing a draft of the new file content.
* The draft content doesn't need to be exactly the same as the existing file; the assistant may skip unchanged lines using comments like `# unchanged` to indicate unchanged sections.
* IMPORTANT: For large files (e.g., > 300 lines), specify the range of lines to edit using `start` and `end` (1-indexed, inclusive). The range should be smaller than 300 lines.
* To append to a file, set both `start` and `end` to `-1`.
* If the file doesn't exist, a new file will be created with the provided content.

**Example 1: general edit for short files**
For example, given an existing file `/path/to/file.py` that looks like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|        self.z = 3
6|
7|print(MyClass().z)
8|print(MyClass().x)
(this is the end of the file)

The assistant wants to edit the file to look like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|
6|print(MyClass().y)
(this is the end of the file)

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=1 end=-1
content=```
class MyClass:
    def __init__(self):
        # no changes before
        self.y = 2
        # self.z is removed

# MyClass().z is removed
print(MyClass().y)
```

**Example 2: append to file for short files**
For example, given an existing file `/path/to/file.py` that looks like this:
(this is the end of the file)
1|class MyClass:
2|    def __init__(self):
3|        self.x = 1
4|        self.y = 2
5|        self.z = 3
6|
7|print(MyClass().z)
8|print(MyClass().x)
(this is the end of the file)

To append the following lines to the file:
```python
print(MyClass().y)
```

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=-1 end=-1
content=```
print(MyClass().y)
```

**Example 3: edit for long files**

Given an existing file `/path/to/file.py` that looks like this:
(1000 more lines above)
1001|class MyClass:
1002|    def __init__(self):
1003|        self.x = 1
1004|        self.y = 2
1005|        self.z = 3
1006|
1007|print(MyClass().z)
1008|print(MyClass().x)
(2000 more lines below)

The assistant wants to edit the file to look like this:

(1000 more lines above)
1001|class MyClass:
1002|    def __init__(self):
1003|        self.x = 1
1004|        self.y = 2
1005|
1006|print(MyClass().y)
(2000 more lines below)

The assistant may produce an edit action like this:
path="/path/to/file.txt" start=1001 end=1008
content=```
class MyClass:
    def __init__(self):
        # no changes before
        self.y = 2
        # self.z is removed

# MyClass().z is removed
print(MyClass().y)
```
"""

FileEditTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='edit_file',
        description=_FILE_EDIT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'thought': {
                    'type': 'string',
                    'description': 'Reasoning about the file edit action.',
                },
                'path': {
                    'type': 'string',
                    'description': 'The absolute path to the file to be edited.',
                },
                'new_content_draft': {
                    'type': 'string',
                    'description': 'A draft of the new content for the file being edited. Note that the assistant may skip unchanged lines.',
                },
                'start': {
                    'type': 'integer',
                    'description': 'The starting line number for the edit (1-indexed, inclusive). Default is 1.',
                },
                'end': {
                    'type': 'integer',
                    'description': 'The ending line number for the edit (1-indexed, inclusive). Default is -1 (end of file).',
                },
            },
            'required': ['path', 'content'],
        },
    ),
)

_BROWSER_DELEGATION = """Delegate the task to another browsing agent.
The assistant should delegate the task if it needs to browse the Internet.
"""

BrowserDelegationTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='delegate_to_browsing_agent',
        description=_BROWSER_DELEGATION,
        parameters={
            'type': 'object',
            'properties': {
                'task': {
                    'type': 'string',
                    'description': 'The task for the browsing agent to execute. It should include all the necessary context and specify what information the browsing agent should return.',
                },
            },
            'required': ['task'],
        },
    ),
)

_FINISH_DESCRIPTION = """Finish the interaction.
* Do this if the task is complete.
* Do this if the assistant cannot proceed further with the task.
"""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finish',
        description=_FINISH_DESCRIPTION,
    ),
)


def response_to_action(response: ModelResponse) -> Action:
    assistant_msg = response.choices[0].message
    if assistant_msg.tool_calls:
        tool_call = assistant_msg.tool_calls[0]
        assert len(assistant_msg.tool_calls) == 1
        ret: Action | None = None
        if tool_call.function.name == 'execute_bash':
            ret = CmdRunAction(**json.loads(tool_call.function.arguments))
        elif tool_call.function.name == 'execute_ipython_cell':
            ret = IPythonRunCellAction(**json.loads(tool_call.function.arguments))
        elif tool_call.function.name == 'message_user':
            ret = MessageAction(**json.loads(tool_call.function.arguments)['content'])
        elif tool_call.function.name == 'delegate_to_browsing_agent':
            ret = AgentDelegateAction(**json.loads(tool_call.function.arguments))
        elif tool_call.function.name == 'finish':
            ret = AgentFinishAction()
        else:
            raise RuntimeError(f'Unknown tool call: {tool_call.function.name}')
    else:
        logger.warning(f'No tool call found in the response: {assistant_msg}')
        ret = MessageAction(content=assistant_msg.content)

    assert ret is not None
    ret.trigger_by_llm_response = response
    return ret


def get_tools(include_browsing_delegate: bool = False) -> list[ChatCompletionToolParam]:
    tools = [CmdRunTool, IPythonTool, FileEditTool, FinishTool]
    if include_browsing_delegate:
        tools.append(BrowserDelegationTool)
    return tools
