from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_GLOB_DESCRIPTION = """Fast file pattern matching tool.
* Supports glob patterns like "**/*.js" or "src/**/*.ts"
* Use this tool when you need to find files by name patterns
* Returns matching file paths sorted by modification time
* Only the first 100 results are returned. Consider narrowing your search with stricter glob patterns or provide path parameter if you need more results.
* When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
"""

GlobTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='glob',
        description=_GLOB_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'pattern': {
                    'type': 'string',
                    'description': 'The glob pattern to match files (e.g., "**/*.js", "src/**/*.ts")',
                },
                'path': {
                    'type': 'string',
                    'description': 'The directory (absolute path) to search in. Defaults to the current working directory.',
                },
            },
            'required': ['pattern'],
        },
    ),
)
