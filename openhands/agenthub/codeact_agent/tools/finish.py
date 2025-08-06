from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import FINISH_TOOL_NAME

_FINISH_DESCRIPTION = """Signals the completion of the current task or conversation.

Use this tool when:
- You have successfully completed the user's requested task
- You cannot proceed further due to technical limitations or missing information

The message should include:
- A clear summary of actions taken and their results
- Any next steps for the user
- Explanation if you're unable to complete the task
- Any follow-up questions if more information is needed
"""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name=FINISH_TOOL_NAME,
        description=_FINISH_DESCRIPTION,
        parameters={
            'type': 'object',
            'required': ['message'],
            'properties': {
                'message': {
                    'type': 'string',
                    'description': 'Final message to send to the user',
                },
            },
        },
    ),
)
