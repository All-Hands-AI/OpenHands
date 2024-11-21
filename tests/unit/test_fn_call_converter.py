from openhands.llm.fn_call_converter import (
    convert_fncall_messages_to_non_fncall_messages,
)


def test_convert_fncall_messages_no_content():
    """Test that messages without content are handled correctly."""
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Hello!'},
        {
            'role': 'assistant',
            'function_call': {'name': 'greet', 'arguments': '{}'},
            'role': 'assistant',
        },  # No content
    ]
    tools = [
        {
            'type': 'function',
            'function': {
                'name': 'greet',
                'description': 'Greet the user',
                'parameters': {'type': 'object', 'properties': {}, 'required': []},
            },
        }
    ]

    # This should not raise a KeyError
    result = convert_fncall_messages_to_non_fncall_messages(
        messages, tools, add_in_context_learning_example=False
    )
    assert isinstance(result, list)
    assert len(result) == len(messages)
