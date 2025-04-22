"""Test that LLM handles description length limits correctly."""

import pytest
from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

from openhands.core.config import LLMConfig
from openhands.llm.fn_call_converter import convert_tools_to_description
from openhands.llm.llm import LLM


def test_description_length_limit():
    """Test that description length is limited for o4-mini model."""
    # Create a tool with a long description
    long_desc = "A" * 2000  # Description longer than 1024 chars
    tool = ChatCompletionToolParam(
        type='function',
        function=ChatCompletionToolParamFunctionChunk(
            name='test_function',
            description=long_desc,
            parameters={
                'type': 'object',
                'properties': {
                    'param1': {
                        'type': 'string',
                        'description': long_desc,
                    }
                },
                'required': ['param1'],
            },
        ),
    )

    # Test with o4-mini model
    config = LLMConfig(model='openai/o4-mini')
    llm = LLM(config)

    # Convert tools to description with max length limit
    desc = convert_tools_to_description([tool], max_desc_length=1024)

    # Verify description is truncated
    assert len(desc.split('\nDescription: ')[1].split('\n')[0]) <= 1024
    assert len(desc.split('param1 (string, required): ')[1].split('\n')[0]) <= 1024

    # Test without length limit
    config = LLMConfig(model='gpt-4')
    llm = LLM(config)

    # Convert tools to description without max length limit
    desc = convert_tools_to_description([tool])

    # Verify description is not truncated
    assert len(desc.split('\nDescription: ')[1].split('\n')[0]) == 2000
    assert len(desc.split('param1 (string, required): ')[1].split('\n')[0]) == 2000
