from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

ViewFileTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='view_file',
        description='View the content of a specified file, optionally within a line range.',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'description': 'Absolute path to the file, e.g. `/workspace/file.py`.',
                    'type': 'string',
                },
                'view_range': {
                    'description': 'Optional line range [start, end] (1-based, inclusive). Shows full file if omitted. `[start, -1]` shows from start to end.',
                    'items': {'type': 'integer'},
                    'type': 'array',
                },
            },
            'required': ['path'],
        },
    ),
)
