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
                'safety_risk': {
                    'type': 'string',
                    'description': "The LLM's assessment of the safety risk of this Python code. This helps the security analyzer determine whether user confirmation is needed.",
                    'enum': ['LOW', 'MEDIUM', 'HIGH'],
                },
            },
            'required': ['code'],
        },
    ),
)
