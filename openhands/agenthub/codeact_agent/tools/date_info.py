from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_DATE_DESCRIPTION = """Use the tool to get the current date."""

DateInfoTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='get_current_date',
        description=_DATE_DESCRIPTION,
    ),
)
