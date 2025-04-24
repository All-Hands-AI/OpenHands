from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FINISH_DESCRIPTION = """Signals the completion of the current task or conversation.

Use this tool when:
- You have successfully completed the user's requested task and saved the final answer to file
- You may not proceed further due to technical limitations or missing information

The message should concise and include:
- The path to the file where the final answer is saved

The task_completed field should be set to True if you believe you have successfully completed the task, and False otherwise.
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
                    'description': 'The final message to the user, including the path to the file where the final answer is saved',
                },
                'task_completed': {
                    'type': 'boolean',
                    'description': "Whether you believe you have successfully completed the user's task",
                },
            },
            'additionalProperties': False,
        },
    ),
)
