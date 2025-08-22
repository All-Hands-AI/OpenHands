from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.llm.tool_names import GEMINI_REPLACE_TOOL_NAME


def create_gemini_replace_tool() -> ChatCompletionToolParam:
    return ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name=GEMINI_REPLACE_TOOL_NAME,
            description='Replace text in a file (Gemini-CLI compatible). old_string must match exactly and uniquely unless expected_replacements > 1. If old_string is empty and file does not exist, create it with new_string.',
            parameters={
                'type': 'object',
                'properties': {
                    'file_path': {
                        'description': 'Absolute path to target file.',
                        'type': 'string',
                    },
                    'old_string': {
                        'description': 'Exact literal text to replace. Include ample context for uniqueness. If empty, creates new file with new_string if file does not exist.',
                        'type': 'string',
                    },
                    'new_string': {
                        'description': 'Replacement text.',
                        'type': 'string',
                    },
                    'expected_replacements': {
                        'description': 'Expected number of replacements. Defaults to 1.',
                        'type': 'integer',
                    },
                },
                'required': ['file_path', 'new_string'],
            },
        ),
    )
