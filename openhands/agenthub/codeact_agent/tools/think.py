from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_THINK_DESCRIPTION = """To ensure a clear record of your work, you must report the reasoning for every significant action you take (e.g., executing a bash command, editing a file, running a test, etc). Use the think tool for this purpose.

Your report must follow this structure:

1. Current Situation: Start with a brief summary of the current context.
2. Options Analysis: Analyze the potential actions you can take.
3. Chosen Action: State the single, most optimal action you've decided on.
4. Justification: Explain why this action is the best available next step for solving the issue.

This information will be saved, allowing you to review your thought process at any time.
"""

ThinkTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='think',
        description=_THINK_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'thought': {'type': 'string', 'description': 'The report that explains your reasoning for taking the next action.'},
            },
            'required': ['thought'],
        },
    ),
)
