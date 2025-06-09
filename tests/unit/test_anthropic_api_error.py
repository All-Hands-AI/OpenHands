import base64
import os
from io import BytesIO

import numpy as np
import pytest
from litellm.exceptions import BadRequestError
from PIL import Image

from openhands.runtime.browser.base64 import image_to_png_base64_url


def create_test_image():
    """Create a simple test image."""
    # Create a simple 10x10 RGB image
    img_array = np.zeros((10, 10, 3), dtype=np.uint8)
    img_array[:, :, 0] = 255  # Red channel
    return Image.fromarray(img_array)


def test_anthropic_api_png_format_error():
    """Test that demonstrates the error when sending a PNG image to Anthropic API."""
    import litellm

    # Skip this test if no Anthropic API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('No Anthropic API key available')

    # Create a test image and convert it to PNG base64
    test_image = create_test_image()
    png_base64 = image_to_png_base64_url(test_image, add_data_prefix=True)

    # Verify the image URL format is PNG
    assert png_base64.startswith('data:image/png;base64,'), (
        f'Expected PNG format, got: {png_base64[:30]}...'
    )

    # Create a message with the PNG image
    messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': "What's in this image?"},
                {'type': 'image_url', 'image_url': {'url': png_base64}},
            ],
        }
    ]

    # Try to call the Anthropic API directly with the PNG image
    # This should raise a BadRequestError about image URL format
    with pytest.raises(BadRequestError) as excinfo:
        litellm.completion(
            model='anthropic/claude-3-opus-20240229', messages=messages, api_key=api_key
        )

    # Verify the error message contains information about image format
    error_message = str(excinfo.value)
    assert 'Image url not in expected format' in error_message, (
        f'Unexpected error message: {error_message}'
    )


def test_anthropic_api_jpeg_format():
    """Test that demonstrates that JPEG format works with Anthropic API."""
    import litellm

    # Skip this test if no Anthropic API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('No Anthropic API key available')

    # Create a test image and convert it to JPEG base64
    test_image = create_test_image()

    # Save as JPEG to BytesIO
    buffer = BytesIO()
    test_image.save(buffer, format='JPEG')
    buffer.seek(0)

    # Convert to base64
    jpeg_base64_data = base64.b64encode(buffer.read()).decode('utf-8')
    jpeg_base64 = f'data:image/jpeg;base64,{jpeg_base64_data}'

    # Verify the image URL format is JPEG
    assert jpeg_base64.startswith('data:image/jpeg;base64,'), (
        f'Expected JPEG format, got: {jpeg_base64[:30]}...'
    )

    # Create a message with the JPEG image
    messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': "What's in this image?"},
                {'type': 'image_url', 'image_url': {'url': jpeg_base64}},
            ],
        }
    ]

    # Try to call the Anthropic API with the JPEG image
    # This should work without errors
    response = litellm.completion(
        model='anthropic/claude-3-opus-20240229',
        messages=messages,
        api_key=api_key,
        max_tokens=100,  # Limit response size for faster test
    )

    # Verify we got a response
    assert response is not None
    assert response.choices[0].message.content is not None
