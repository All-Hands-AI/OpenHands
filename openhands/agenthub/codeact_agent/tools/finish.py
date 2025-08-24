from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import FINISH_TOOL_NAME

_FINISH_DESCRIPTION = """Signals the completion of the current task and provides a summary of actions taken and their results. Call this tool once you have fixed the issue and verified that your solution works properly. Also, if you bumped into an unexpected problem that prevents you from fixing the issue, explain this problem and list all the workaround attempts that you tried.
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
