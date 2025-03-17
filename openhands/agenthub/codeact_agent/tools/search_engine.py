from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_SEARCH_ENGINE_DESCRIPTION = """Execute a web search query (similar to Google search).

NOTE: When you need to search for information online, please use the `search_engine` tool rather than the `browser` or `web_read` tools. The `search_engine` tool connects directly to a search engine, which will help avoid CAPTCHA challenges that would otherwise block your access.
"""

SearchEngineTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='search_engine',
        description=_SEARCH_ENGINE_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The web search query (must be a non-empty string).',
                },
            },
            'required': ['query'],
        },
    ),
)
