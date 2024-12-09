import pytest
from litellm import ChatCompletionMessageToolCall

from openhands.core.message import (
    ImageContent,
    Message,
    TextContent,
    ToolCallContent,
    ToolResponseContent,
)


@pytest.fixture
def base_message():
    return Message(
        role='user',
        content=[TextContent(text='Sample message', cache_prompt=False)],
        cache_enabled=False,
        vision_enabled=False,
        function_calling_enabled=False,
    )


def test_serializer_prompt_caching_enabled(base_message):
    """Test serialization with prompt caching enabled and others disabled."""
    base_message.cache_enabled = True
    # Enable cache_prompt on TextContent
    base_message.content[0].cache_prompt = True
    serialized = base_message.serialize_model()

    expected = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'Sample message',
                'cache_control': {'type': 'ephemeral'},
            },
        ],
    }

    assert serialized == expected


def test_serializer_vision_enabled(base_message):
    """Test serialization with vision enabled and others disabled."""
    image = ImageContent(image_urls=['http://example.com/image.png'])
    base_message.vision_enabled = True
    base_message.content.append(image)
    serialized = base_message.serialize_model()

    expected = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'Sample message',
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image.png'},
            },
        ],
    }

    assert serialized == expected
    assert base_message.contains_image is True


def test_serializer_function_calling_enabled(base_message):
    """Test serialization with function calling enabled and others disabled."""
    base_message.function_calling_enabled = True
    serialized = base_message.serialize_model()

    expected = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'Sample message',
            },
        ],
    }

    assert serialized == expected


def test_serializer_all_enabled(base_message):
    """Test serialization with prompt caching, vision, and function calling enabled."""
    image = ImageContent(image_urls=['http://example.com/image.png'])
    base_message.cache_enabled = True
    base_message.vision_enabled = True
    base_message.function_calling_enabled = True
    # Enable cache_prompt on TextContent
    base_message.content[0].cache_prompt = True
    base_message.content.append(image)
    serialized = base_message.serialize_model()

    expected = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'Sample message',
                'cache_control': {'type': 'ephemeral'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image.png'},
            },
        ],
    }

    assert serialized == expected
    assert base_message.contains_image is True


def test_serializer_all_disabled(base_message):
    """Test serialization with prompt caching, vision, and function calling disabled."""
    serialized = base_message.serialize_model()

    expected = {
        'role': 'user',
        'content': 'Sample message',
    }

    assert serialized == expected
    assert base_message.contains_image is False


def test_serializer_combined_features():
    """Test serialization with a combination of enabled and disabled features."""
    # Enable prompt caching and vision, disable function calling
    message = Message(
        role='assistant',
        content=[
            TextContent(text='Here is an image:', cache_prompt=False),
            ImageContent(image_urls=['http://example.com/image1.png']),
            ImageContent(image_urls=['http://example.com/image2.png']),
        ],
        cache_enabled=True,
        vision_enabled=True,
        function_calling_enabled=False,
    )
    # Enable cache_prompt on the first TextContent
    message.content[0].cache_prompt = True
    serialized = message.serialize_model()

    expected = {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': 'Here is an image:',
                'cache_control': {'type': 'ephemeral'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image1.png'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image2.png'},
            },
        ],
    }

    assert serialized == expected
    assert message.contains_image is True


def test_serializer_no_content():
    """Test serialization when there is no content."""
    message = Message(
        role='system',
        content=[],
        cache_enabled=False,
        vision_enabled=False,
        function_calling_enabled=False,
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'system',
        'content': '',
    }

    assert serialized == expected
    assert message.contains_image is False


def test_serializer_partial_content():
    """Test serialization with mixed content types and some features enabled."""
    message = Message(
        role='user',
        content=[
            TextContent(text='Start of the message.', cache_prompt=True),
            ImageContent(image_urls=['http://example.com/image1.png']),
            TextContent(text='End of the message.', cache_prompt=False),
        ],
        cache_enabled=False,
        vision_enabled=True,
        function_calling_enabled=False,
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'Start of the message.',
                'cache_control': {'type': 'ephemeral'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image1.png'},
            },
            {
                'type': 'text',
                'text': 'End of the message.',
            },
        ],
    }

    assert serialized == expected
    assert message.contains_image is True


def test_message_with_vision_enabled():
    text_content1 = TextContent(text='This is a text message', cache_prompt=True)
    image_content1 = ImageContent(
        image_urls=['http://example.com/image1.png', 'http://example.com/image2.png']
    )
    text_content2 = TextContent(text='This is another text message', cache_prompt=False)
    image_content2 = ImageContent(
        image_urls=['http://example.com/image3.png', 'http://example.com/image4.png']
    )

    message: Message = Message(
        role='user',
        content=[text_content1, image_content1, text_content2, image_content2],
        vision_enabled=True,
    )
    serialized_message: dict = message.serialize_model()

    expected_serialized_message = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'This is a text message',
                'cache_control': {'type': 'ephemeral'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image1.png'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image2.png'},
            },
            {
                'type': 'text',
                'text': 'This is another text message',
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image3.png'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image4.png'},
            },
        ],
    }

    assert serialized_message == expected_serialized_message
    assert message.contains_image is True


def test_message_with_only_text_content_and_vision_enabled():
    text_content1 = TextContent(text='This is a text message')
    text_content2 = TextContent(text='This is another text message')

    message: Message = Message(
        role='user', content=[text_content1, text_content2], vision_enabled=True
    )
    serialized_message: dict = message.serialize_model()

    expected_serialized_message = {
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'This is a text message'},
            {'type': 'text', 'text': 'This is another text message'},
        ],
    }

    assert serialized_message == expected_serialized_message
    assert message.contains_image is False


def test_message_with_mixed_content_and_vision_disabled():
    # Create a message with both text and image content
    text_content1 = TextContent(text='This is a text message', cache_prompt=True)
    image_content1 = ImageContent(
        image_urls=['http://example.com/image1.png', 'http://example.com/image2.png']
    )
    text_content2 = TextContent(text='This is another text message', cache_prompt=False)
    image_content2 = ImageContent(
        image_urls=['http://example.com/image3.png', 'http://example.com/image4.png']
    )

    # Initialize Message with vision disabled
    message: Message = Message(
        role='user',
        content=[text_content1, image_content1, text_content2, image_content2],
        vision_enabled=False,
        cache_enabled=True,
    )
    serialized_message: dict = message.serialize_model()

    # Expected serialization ignores images and concatenates text
    expected_serialized_message = {
        'role': 'user',
        'content': [
            {
                'type': 'text',
                'text': 'This is a text message',
                'cache_control': {'type': 'ephemeral'},
            },
            {
                'type': 'text',
                'text': 'This is another text message',
            },
        ],
    }

    # Assert serialized message matches expectation
    assert serialized_message == expected_serialized_message
    # Assert that images exist in the original message
    assert message.contains_image


def test_serializer_function_calling_enabled_with_tool_calls():
    """Test serialization with function calling enabled, assistant calling a tool, and tool responding."""
    # Create a tool call from the assistant
    tool_call = ChatCompletionMessageToolCall(
        id='call-id-123',
        type='function',
        function={
            'id': 'tool-call-123',
            'name': 'execute_bash',
            'arguments': '{"command": "ls -la"}',
        },
    )

    assistant_message = Message(
        role='assistant',
        content=[
            TextContent(
                text='Sure, executing the command.', type='text', cache_prompt=False
            )
        ],
        cache_enabled=True,
        vision_enabled=False,
        function_calling_enabled=True,
        tool_calls=[tool_call],
    )

    # Create a tool response message
    tool_response = Message(
        role='tool',
        content=[TextContent(text='./test.sh', type='text')],  # Tool response
        cache_enabled=False,
        vision_enabled=False,
        function_calling_enabled=True,
        tool_call_id='tool-call-123',
        name='execute_bash',
    )

    # Serialize assistant message
    serialized_assistant = assistant_message.serialize_model()

    expected_assistant = {
        'role': 'assistant',
        'content': [
            {
                'type': 'text',
                'text': 'Sure, executing the command.',
            },
        ],
        'tool_calls': [
            {
                'id': 'call-id-123',
                'type': 'function',
                'function': {
                    'id': 'tool-call-123',
                    'name': 'execute_bash',
                    'arguments': '{"command": "ls -la"}',
                },
            }
        ],
    }

    assert serialized_assistant == expected_assistant

    # Serialize tool response message
    serialized_tool = tool_response.serialize_model()

    expected_tool = {
        'role': 'tool',
        'content': [
            {
                'type': 'text',
                'text': './test.sh',
            }
        ],
        'tool_call_id': 'tool-call-123',
        'name': 'execute_bash',
    }

    assert serialized_tool == expected_tool


import pytest


def test_serializer_function_calling_disabled_with_tool_calls():
    """Test serialization with function calling disabled, assistant calling a tool, and tool responding."""
    # Create a tool call from the assistant
    tool_call = ChatCompletionMessageToolCall(
        id='call-id-456',
        type='function',
        function={
            'id': 'tool-call-456',
            'name': 'execute_ipython_cell',
            'arguments': '{"code": "print(\\"Hello World\\")"}',
        },
    )

    assistant_message = Message(
        role='assistant',
        content=[
            TextContent(
                text='Executing your Python code.', type='text', cache_prompt=False
            )
        ],
        cache_enabled=False,
        vision_enabled=False,
        function_calling_enabled=False,
        tool_calls=[tool_call],
    )

    # Create a tool response message
    tool_response = Message(
        role='tool',
        content=[
            TextContent(text='Hello World', type='text')
        ],  # Tool response content can be empty or have relevant data
        cache_enabled=False,
        vision_enabled=False,
        function_calling_enabled=False,
        tool_call_id='tool-call-456',
        name='execute_ipython_cell',
    )

    # Serialize assistant message
    serialized_assistant = assistant_message.serialize_model()

    # Since function_calling_enabled is False, tool_calls should be converted into content
    # Expected format based on convert_tool_call_to_string():
    expected_assistant_content = (
        'Executing your Python code.'
        '\n<function=execute_ipython_cell>'
        '\n<parameter=command>print("Hello World")</parameter>'
        '\n</function>'
    )

    expected_assistant = {
        'role': 'assistant',
        'content': expected_assistant_content,
    }

    assert (
        serialized_assistant == expected_assistant
    ), f'Serialized assistant message does not match expected output.\nSerialized: {serialized_assistant}\nExpected: {expected_assistant}'

    # Serialize tool response message
    serialized_tool = tool_response.serialize_model()

    # Since function_calling_enabled is False, tool_call_id and name should not be serialized
    expected_tool = {
        'role': 'tool',
        'content': 'Hello World',
    }

    assert (
        serialized_tool == expected_tool
    ), f'Serialized tool message does not match expected output.\nSerialized: {serialized_tool}\nExpected: {expected_tool}'


def test_tool_call_native_serialization():
    """Test serialization of tool calls with native function calling"""
    tool_call = ChatCompletionMessageToolCall(
        id='call-123',
        type='function',
        function={'name': 'execute_bash', 'arguments': '{"command": "ls -la"}'},
    )
    message = Message(
        role='assistant',
        content=[],  # Empty content for tool calls
        tool_calls=[tool_call],
        function_calling_enabled=True,
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'assistant',
        'content': None,  # null content as per API
        'tool_calls': [
            {
                'id': 'call-123',
                'type': 'function',
                'function': {
                    'name': 'execute_bash',
                    'arguments': '{"command": "ls -la"}',
                },
            }
        ],
    }

    assert serialized == expected


def test_tool_call_string_serialization():
    """Test serialization of tool calls with string format"""
    tool_call = ToolCallContent(
        function_name='execute_bash',
        function_arguments='{"command": "ls -la"}',
        tool_call_id='call-123',
    )
    message = Message(
        role='assistant', content=[tool_call], function_calling_enabled=False
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'assistant',
        'content': '<function=execute_bash>\n<parameter=command>ls -la</parameter>\n</function>',
    }

    assert serialized == expected


def test_tool_response_native_serialization():
    """Test serialization of tool responses with native function calling"""
    message = Message(
        role='tool',
        content=[
            TextContent(text='total 0\ndrwxr-xr-x  3 user  group   96 Mar 17 10:00 .')
        ],
        tool_call_id='call-123',
        name='execute_bash',
        function_calling_enabled=True,
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'tool',
        'content': 'total 0\ndrwxr-xr-x  3 user  group   96 Mar 17 10:00 .',
        'tool_call_id': 'call-123',
        'name': 'execute_bash',
    }

    assert serialized == expected


def test_tool_response_string_serialization():
    """Test serialization of tool responses with string format"""
    tool_response = ToolResponseContent(
        tool_call_id='call-123',
        name='execute_bash',
        content='total 0\ndrwxr-xr-x  3 user  group   96 Mar 17 10:00 .',
    )
    message = Message(
        role='tool', content=[tool_response], function_calling_enabled=False
    )
    serialized = message.serialize_model()

    expected = {
        'role': 'tool',
        'content': 'EXECUTION RESULT of [execute_bash]:\ntotal 0\ndrwxr-xr-x  3 user  group   96 Mar 17 10:00 .',
    }

    assert serialized == expected
