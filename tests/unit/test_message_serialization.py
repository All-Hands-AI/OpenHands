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
