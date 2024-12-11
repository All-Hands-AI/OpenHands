from unittest.mock import patch

from openhands.core.config import LLMConfig
from openhands.core.message import ImageContent, Message, TextContent
from openhands.llm.llm import LLM


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


def test_empty_content_serialization():
    """Test empty content serialization behavior for different providers/models."""
    # Create a message with empty content
    message = Message(
        role='tool',
        content=[TextContent(text='')],
        function_calling_enabled=True,
        tool_call_id='tool_123',
        name='test_tool',
    )
    # by default, empty content should be preserved
    message.strip_empty_content = False
    serialized = message.model_dump()

    assert 'content' in serialized
    assert serialized['content'] == [{'type': 'text', 'text': ''}]
    assert serialized['tool_call_id'] == 'tool_123'
    assert serialized['name'] == 'test_tool'
    assert serialized['role'] == 'tool'

    # if the flag is set, empty content should be stripped
    message.strip_empty_content = True
    serialized = message.model_dump()

    assert 'content' not in serialized
    assert serialized['tool_call_id'] == 'tool_123'
    assert serialized['name'] == 'test_tool'
    assert serialized['role'] == 'tool'


def test_empty_content_with_multiple_items():
    """Test empty content serialization with multiple content items."""
    message = Message(
        role='user',
        content=[
            TextContent(text=''),
            ImageContent(image_urls=['http://example.com/img.jpg']),
            TextContent(text=''),
        ],
        vision_enabled=True,
    )

    # Even with strip_empty_content=True, content should not be stripped
    # if there are non-empty items
    message.strip_empty_content = True
    serialized = message.model_dump()

    assert 'content' in serialized
    assert len(serialized['content']) == 3
    assert serialized['content'][1]['type'] == 'image_url'


def test_llm_empty_content_stripping_list_serialization():
    """Test empty content stripping with list serialization for Bedrock models."""
    # To workaround a bug in Bedrock, we strip the content if it's empty
    # See https://github.com/All-Hands-AI/OpenHands/issues/5492
    bedrock_config = LLMConfig(
        model='bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0'
    )
    bedrock_llm = LLM(config=bedrock_config)

    # Test with list serialization (vision enabled)
    message = Message(
        role='assistant',
        content=[TextContent(text='')],
        vision_enabled=True,  # Enable vision to force list serialization
    )

    # Format message for the LLM - this should set strip_empty_content=True
    formatted_messages = bedrock_llm.format_messages_for_llm(message)
    assert len(formatted_messages) == 1
    assert 'content' not in formatted_messages[0]

    # Test non-Bedrock model with list serialization
    regular_config = LLMConfig(model='claude-3-5-sonnet-20241022')
    regular_llm = LLM(config=regular_config)

    message = Message(
        role='assistant', content=[TextContent(text='')], vision_enabled=True
    )

    # Format message for the LLM - this should preserve empty content
    formatted_messages = regular_llm.format_messages_for_llm(message)
    assert len(formatted_messages) == 1
    assert 'content' in formatted_messages[0]
    assert formatted_messages[0]['content'] == [{'type': 'text', 'text': ''}]

    # Test Bedrock as custom provider with list serialization
    bedrock_provider_config = LLMConfig(
        model='claude-3-5-sonnet-20241022-v2:0', custom_llm_provider='bedrock'
    )
    bedrock_provider_llm = LLM(config=bedrock_provider_config)

    message = Message(
        role='assistant', content=[TextContent(text='')], vision_enabled=True
    )

    # Format message using the LLM - this should set strip_empty_content=True
    formatted_messages = bedrock_provider_llm.format_messages_for_llm(message)
    assert len(formatted_messages) == 1
    assert 'content' not in formatted_messages[0]


def test_llm_empty_content_string_serialization():
    """Test empty content with string serialization (no vision/cache/function flags)."""
    bedrock_config = LLMConfig(
        model='bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0'
    )

    # Use patch to mock the LLM methods that determine serialization mode
    with patch.multiple(
        'openhands.llm.llm.LLM',
        is_function_calling_active=lambda self: False,
        vision_is_active=lambda self: False,
        is_caching_prompt_active=lambda self: False,
    ):
        bedrock_llm = LLM(config=bedrock_config)
        message = Message(role='assistant', content=[TextContent(text='')])

        # Format message using the LLM - this should use string serialization
        formatted_messages = bedrock_llm.format_messages_for_llm(message)
        assert len(formatted_messages) == 1
        assert 'content' in formatted_messages[0]
        assert formatted_messages[0]['content'] == ''
