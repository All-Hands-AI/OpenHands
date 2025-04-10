from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FINISH_DESCRIPTION = """Signals the completion of the conversation.

Use this tool when all tasks in plan have been completed or when the user has ended the conversation.

The message should include:
- A clear summary of tasks taken and their results
- Any next steps for the user
- Explanation if you're unable to complete the user's request
- Any follow-up questions if more information is needed

The task_completed field should be set to True if you believed you have completed the user's request, and False otherwise.
"""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finish',
        description=_FINISH_DESCRIPTION,
        parameters={
            'type': 'object',
            'required': ['message', 'task_completed'],
            'properties': {
                'message': {
                    'type': 'string',
                    'description': 'Final message to send to the user',
                },
                'task_completed': {
                    'type': 'string',
                    'enum': ['true', 'false', 'partial'],
                    'description': 'Whether you have completed the task.',
                },
            },
        },
    ),
)
