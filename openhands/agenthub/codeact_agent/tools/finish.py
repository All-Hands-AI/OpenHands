from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FINISH_DESCRIPTION = """Finish the interaction when the task is complete OR if the assistant cannot proceed further with the task."""

FinishTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='finish',
        description=_FINISH_DESCRIPTION,
    ),
)
