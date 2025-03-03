from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_SEARCH_ENGINE_DESCRIPTION = """Execute a web search query (similar to Google search).

You MUST use this tool as a search engine and find URLs of webpages that are relevant to the search query.
NOTE: Do NOT use the browser tool to search using Google or Bing since you will be blocked by CAPTCHAs.
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
