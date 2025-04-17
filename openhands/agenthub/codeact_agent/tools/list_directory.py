from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

ListDirectoryTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='list_directory',
        description='List non-hidden files and directories within a specified directory path, up to 2 levels deep.',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'description': 'Absolute path to the directory, e.g. `/workspace/subdir`.',
                    'type': 'string',
                },
            },
            'required': ['path'],
        },
    ),
)
