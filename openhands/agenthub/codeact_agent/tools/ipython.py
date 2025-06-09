from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_IPYTHON_DESCRIPTION = """Run a cell of Python code in an IPython environment.
* The assistant should define variables and import packages before using them.
* The variable defined in the IPython environment will not be available outside the IPython environment (e.g., in terminal).
"""

IPythonTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='execute_ipython_cell',
        description=_IPYTHON_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'The Python code to execute. Supports magic commands like %pip.',
                },
            },
            'required': ['code'],
        },
    ),
)
