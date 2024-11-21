# CodeAct Agent Framework

This folder implements the CodeAct idea ([paper](https://arxiv.org/abs/2402.01030), [tweet](https://twitter.com/xingyaow_/status/1754556835703751087)) that consolidates LLM agents’ **act**ions into a unified **code** action space for both *simplicity* and *performance* (see paper for more details).

The conceptual idea is illustrated below. At each turn, the agent can:

1. **Converse**: Communicate with humans in natural language to ask for clarification, confirmation, etc.
2. **CodeAct**: Choose to perform the task by executing code
   - Execute any valid Linux `bash` command
   - Execute any valid `Python` code with [an interactive Python interpreter](https://ipython.org/). This is simulated through `bash` command, see plugin system below for more details.

![image](https://github.com/All-Hands-AI/OpenHands/assets/38853559/92b622e3-72ad-4a61-8f41-8c040b6d5fb3)

## Adding New Tools

The CodeAct agent uses a function calling interface to define tools that the agent can use. Tools are defined in `function_calling.py` using the `ChatCompletionToolParam` class from `litellm`. Each tool consists of:

1. A description string that explains what the tool does and how to use it
2. A tool definition using `ChatCompletionToolParam` that specifies:
   - The tool's name
   - The tool's parameters and their types
   - Required vs optional parameters

Here's an example of how a tool is defined:

```python
MyTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='my_tool',
        description='Description of what the tool does and how to use it',
        parameters={
            'type': 'object',
            'properties': {
                'param1': {
                    'type': 'string',
                    'description': 'Description of parameter 1',
                },
                'param2': {
                    'type': 'integer',
                    'description': 'Description of parameter 2',
                },
            },
            'required': ['param1'],  # List required parameters here
        },
    ),
)
```

To add a new tool:

1. Define your tool in `function_calling.py` following the pattern above
2. Add your tool to the `get_tools()` function in `function_calling.py`
3. Implement the corresponding action handler in the agent to process the tool's invocation

The agent currently supports several built-in tools:
- `execute_bash`: Execute bash commands
- `execute_ipython_cell`: Run Python code in IPython
- `browser`: Interact with a web browser
- `str_replace_editor`: Edit files using string replacement
- `edit_file`: Edit files using LLM-based editing

Tools can be enabled/disabled through configuration parameters:
- `codeact_enable_browsing`: Enable browser interaction
- `codeact_enable_jupyter`: Enable IPython code execution
- `codeact_enable_llm_editor`: Enable LLM-based file editing (if disabled, uses string replacement editor instead)
