from litellm import ChatCompletionMessageToolCall

from openhands.core.message import ImageContent, Message, TextContent


def test_message_with_vision_enabled():
    text_content1 = TextContent(text='This is a text message')
    image_content1 = ImageContent(
        image_urls=['http://example.com/image1.png', 'http://example.com/image2.png']
    )
    text_content2 = TextContent(text='This is another text message')
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
            {'type': 'text', 'text': 'This is a text message'},
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image1.png'},
            },
            {
                'type': 'image_url',
                'image_url': {'url': 'http://example.com/image2.png'},
            },
            {'type': 'text', 'text': 'This is another text message'},
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


def test_message_with_only_text_content_and_vision_disabled():
    text_content1 = TextContent(text='This is a text message')
    text_content2 = TextContent(text='This is another text message')

    message: Message = Message(
        role='user', content=[text_content1, text_content2], vision_enabled=False
    )
    serialized_message: dict = message.serialize_model()

    expected_serialized_message = {
        'role': 'user',
        'content': 'This is a text message\nThis is another text message',
    }

    assert serialized_message == expected_serialized_message
    assert message.contains_image is False


def test_message_with_mixed_content_and_vision_disabled():
    # Create a message with both text and image content
    text_content1 = TextContent(text='This is a text message')
    image_content1 = ImageContent(
        image_urls=['http://example.com/image1.png', 'http://example.com/image2.png']
    )
    text_content2 = TextContent(text='This is another text message')
    image_content2 = ImageContent(
        image_urls=['http://example.com/image3.png', 'http://example.com/image4.png']
    )

    # Initialize Message with vision disabled
    message: Message = Message(
        role='user',
        content=[text_content1, image_content1, text_content2, image_content2],
        vision_enabled=False,
    )
    serialized_message: dict = message.serialize_model()

    # Expected serialization ignores images and concatenates text
    expected_serialized_message = {
        'role': 'user',
        'content': 'This is a text message\nThis is another text message',
    }

    # Assert serialized message matches expectation
    assert serialized_message == expected_serialized_message
    # Assert that images exist in the original message
    assert message.contains_image


def test_message_tool_call_serialization():
    """Test that tool calls are properly serialized into dicts for token counting."""
    # Create a tool call
    tool_call = ChatCompletionMessageToolCall(
        id='call_123',
        type='function',
        function={'name': 'test_function', 'arguments': '{"arg1": "value1"}'},
    )

    # Create a message with the tool call
    message = Message(
        role='assistant',
        content=[TextContent(text='Test message')],
        tool_calls=[tool_call],
    )

    # Serialize the message
    serialized = message.model_dump()

    # Check that tool calls are properly serialized
    assert 'tool_calls' in serialized
    assert isinstance(serialized['tool_calls'], list)
    assert len(serialized['tool_calls']) == 1

    tool_call_dict = serialized['tool_calls'][0]
    assert isinstance(tool_call_dict, dict)
    assert tool_call_dict['id'] == 'call_123'
    assert tool_call_dict['type'] == 'function'
    assert tool_call_dict['function']['name'] == 'test_function'
    assert tool_call_dict['function']['arguments'] == '{"arg1": "value1"}'


def test_message_tool_response_serialization():
    """Test that tool responses are properly serialized."""
    # Create a message with tool response
    message = Message(
        role='tool',
        content=[TextContent(text='Function result')],
        tool_call_id='call_123',
        name='test_function',
    )

    # Serialize the message
    serialized = message.model_dump()

    # Check that tool response fields are properly serialized
    assert 'tool_call_id' in serialized
    assert serialized['tool_call_id'] == 'call_123'
    assert 'name' in serialized
    assert serialized['name'] == 'test_function'
