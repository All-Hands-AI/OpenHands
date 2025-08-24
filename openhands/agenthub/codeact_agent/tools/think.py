from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_THINK_DESCRIPTION = """This tool logs your thoughts whenever you are analyzing complex information and making decisions. This tool does not execute or change any code. You should call this tool in the following situations:

1. Exploring a code repository and deciding which source code files are relevant to the given issue.
2. Brainstorming various ways of fixing the bug.
3. Analyzing test results, and thinking how to fix failing tests.
4. Planning a complex refactoring.
5. Making architecture decisions that require analyzing pros and cons of alternative design options.
6. Troubleshooting unexpected problems.
"""

ThinkTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='think',
        description=_THINK_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'thought': {'type': 'string', 'description': 'The thought that should be logged.'},
            },
            'required': ['thought'],
        },
    ),
)
