from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_CONDENSATION_REQUEST_DESCRIPTION = 'Request a condensation of the conversation history when the context becomes too long or when you need to focus on the most relevant information.'

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
