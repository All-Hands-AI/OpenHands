from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FINISH_DESCRIPTION = """Signals the completion of the current task or conversation.

Use this tool when:
- You have successfully completed the user's requested task
- You cannot proceed further due to technical limitations or missing information

The message should include:
- A clear summary of actions taken and their results
- Any next steps for the user
- Explanation if you're unable to complete the task
- Any follow-up questions if more information is needed

The task_completed field should be set to True if you believed you have completed the task, and False otherwise.
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
