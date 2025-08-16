from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_READ_FILE_TOOL_NAME


def create_gemini_read_file_tool() -> ChatCompletionToolParam:
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_READ_FILE_TOOL_NAME,
            description='Read and return raw file contents. Use absolute paths inside /workspace. For text files you can optionally provide offset & limit (0-based), otherwise the entire file is returned. Images and PDFs are returned as data URLs.',
            parameters={
                'type': 'object',
                'properties': {
                    'path': {
                        'description': 'Absolute path to file, e.g. /workspace/file.py',
                        'type': 'string',
                    },
                    'offset': {
                        'description': 'Optional line offset (0-based) for text files. Requires limit to be set.',
                        'type': 'integer',
                    },
                    'limit': {
                        'description': 'Optional max number of lines to read for text files.',
                        'type': 'integer',
                    },
                },
                'required': ['path'],
            },
        ),
    )
