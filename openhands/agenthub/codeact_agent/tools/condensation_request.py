from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_CONDENSATION_REQUEST_DESCRIPTION = """Request a condensation of the conversation history when the context becomes too long or when you need to focus on the most relevant information.

This tool helps manage conversation context by requesting a summary of the conversation history. Use it when:
1. The conversation has become very long and you need to reduce context size
2. You want to focus on the most important information from the conversation
3. You're experiencing issues with context limits

The tool takes no arguments and simply requests the system to condense the conversation history."""

CondensationRequestTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='request_condensation',
        description=_CONDENSATION_REQUEST_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {},
            'required': [],
        },
    ),
)