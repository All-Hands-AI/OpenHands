from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from openhands.core.message import ImageContent, Message, TextContent
from openhands.runtime.browser.base64 import image_to_png_base64_url


def create_test_image():
    """Create a simple test image."""
    # Create a simple 10x10 RGB image
    img_array = np.zeros((10, 10, 3), dtype=np.uint8)
    img_array[:, :, 0] = 255  # Red channel
    return Image.fromarray(img_array)


def test_anthropic_image_format_issue():
    """Test that demonstrates the issue with image format for Anthropic."""
    # Create a test image
    test_image = create_test_image()

    # Convert to PNG base64 URL (this is what happens in the browser environment)
    screenshot = image_to_png_base64_url(test_image, add_data_prefix=True)

    # Verify the format
    assert screenshot.startswith('data:image/png;base64,'), (
        f"Expected 'data:image/png;base64,' but got {screenshot[:30]}..."
    )

    # Create a message with the screenshot
    message = Message(
        role='user',
        content=[
            TextContent(text="What's in this image?"),
            ImageContent(image_urls=[screenshot]),
        ],
        vision_enabled=True,
    )

    # Serialize the message for litellm
    serialized_message = message.serialize_model()

    # Verify the serialized message
    assert serialized_message['role'] == 'user'
    assert isinstance(serialized_message['content'], list)
    assert len(serialized_message['content']) == 2
    assert serialized_message['content'][0]['type'] == 'text'
    assert serialized_message['content'][1]['type'] == 'image_url'
    assert 'url' in serialized_message['content'][1]['image_url']
    assert serialized_message['content'][1]['image_url']['url'] == screenshot

    # Mock the litellm.completion function to simulate the error
    with patch('litellm.completion') as mock_completion:
        # Configure the mock to raise an exception
        mock_completion.side_effect = Exception(
            """Image url not in expected format. Example Expected input - "image_url": "data:image/jpeg;base64,{base64_image}". Supported formats - ['image/jpeg', 'image/png', 'image/gif', 'image/webp']."""
        )

        # Try to call the Anthropic API through litellm
        with pytest.raises(Exception) as excinfo:
            import litellm

            litellm.completion(
                model='anthropic/claude-3-opus-20240229',
                messages=[serialized_message],
                api_key='fake_api_key',
            )

        # Verify the error message
        error_message = str(excinfo.value)
        assert 'Image url not in expected format' in error_message
        assert 'data:image/jpeg;base64' in error_message
