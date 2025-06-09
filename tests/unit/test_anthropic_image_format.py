import os

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


def test_anthropic_image_format_issue(caplog):
    """Test that demonstrates the issue with image format for Anthropic."""
    # Skip if no API key
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        pytest.skip('ANTHROPIC_API_KEY not set')

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

    # Try to call the Anthropic API through litellm
    # This actually succeeds with PNG format, which is surprising
    import litellm

    try:
        print('\n\nTesting with PNG format:')
        response = litellm.completion(
            model='anthropic/claude-3-opus-20240229',
            messages=[serialized_message],
            api_key=anthropic_api_key,
        )
        print(f'Response: {response}')
        print('PNG format works with Anthropic API directly!')

        # Let's also try with a JPEG format to compare
        import base64
        import io

        # Convert the test image to JPEG
        buffered = io.BytesIO()
        test_image.save(buffered, format='JPEG')
        jpeg_base64 = base64.b64encode(buffered.getvalue()).decode()
        jpeg_url = f'data:image/jpeg;base64,{jpeg_base64}'

        # Create a message with the JPEG screenshot
        jpeg_message = Message(
            role='user',
            content=[
                TextContent(text="What's in this JPEG image?"),
                ImageContent(image_urls=[jpeg_url]),
            ],
            vision_enabled=True,
        )

        # Serialize the message for litellm
        jpeg_serialized_message = jpeg_message.serialize_model()

        # Try with JPEG format
        print('\n\nTesting with JPEG format:')
        jpeg_response = litellm.completion(
            model='anthropic/claude-3-opus-20240229',
            messages=[jpeg_serialized_message],
            api_key=anthropic_api_key,
        )
        print(f'JPEG Response: {jpeg_response}')
        print('JPEG format also works with Anthropic API directly!')

    except Exception as e:
        print(f'Error: {str(e)}')
        raise
