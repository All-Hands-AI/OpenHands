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
                'start_date': {
                    'type': 'string',
                    'description': 'Optional parameter to retrieve only those links published after the date specified by the start_date parameter. The start_date string MUST be specified in ISO 8601 format. Example formats: "2023-12-17T00:00:00.000Z" OR "2024-01-01"',
                },
            },
            'required': ['query'],
        },
    ),
)
