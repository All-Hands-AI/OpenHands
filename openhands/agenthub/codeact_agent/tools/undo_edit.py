from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

UndoEditTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='undo_edit',
        description='Revert the last edit made to the specified file.',
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'description': 'Absolute path to the file for which to undo the last edit, e.g. `/workspace/file.py`.',
                    'type': 'string',
                },
            },
            'required': ['path'],
        },
    ),
)
