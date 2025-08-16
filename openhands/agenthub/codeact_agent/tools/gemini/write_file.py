from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_WRITE_FILE_TOOL_NAME


def create_gemini_write_file_tool() -> ChatCompletionToolParam:
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_WRITE_FILE_TOOL_NAME,
            description='Overwrite or create a file with provided content. Entire-file write. Parent directories are created as needed.',
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': 'Absolute path to file to write, e.g. /workspace/file.py',
                        'type': 'string',
                    },
                    'content': {
                        'description': 'Full content to write (UTF-8).',
                        'type': 'string',
                    },
                },
                'required': ['file_path', 'content'],
            },
        ),
    )
