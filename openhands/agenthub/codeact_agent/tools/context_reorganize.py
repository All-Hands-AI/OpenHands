from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_CONTEXT_REORGANIZE_DESCRIPTION = """Reorganize your context when it becomes too large, contains redundant information, or has outdated content.

Common use cases:
1. When the context becomes too large and you need to summarize previous interactions
2. When the user explicitly requests context reorganization
3. When there's redundant information in the context
4. When the context contains outdated information (like old versions of files)

This tool will create a new condensed context with:
1. A structured summary of the important information and insights from the conversation
2. The current versions of important files from the workspace

Parameters:
- files: A list of files from the workspace that should be added to the context
- summary: A structured summary of what is going on, containing all important information and insights
"""

ContextReorganizeTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='context_reorganize',
        description=_CONTEXT_REORGANIZE_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'files': {
                    'type': 'array',
                    'description': 'A list of files from the workspace that should be added to the context. Each file is an object with "path" (required) and "view_range" (optional) properties.',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'path': {
                                'type': 'string',
                                'description': 'Absolute path to the file, e.g. "/workspace/file.py"',
                            },
                            'view_range': {
                                'type': 'array',
                                'description': 'Optional line range to view. If none is given, the full file is shown. Format: [start_line, end_line]. Use [start_line, -1] to show all lines from start_line to the end of the file.',
                                'items': {'type': 'integer'},
                            },
                        },
                        'required': ['path'],
                    },
                },
                'summary': {
                    'type': 'string',
                    'description': 'A structured summary of what is going on. This needs to contain all important information and insights that are in the current conversation.',
                },
            },
            'required': ['files', 'summary'],
        },
    ),
)
