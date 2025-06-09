import os

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


def test_anthropic_direct_api_call():
    """Test that directly calls the Anthropic API to reproduce the error.

    This test is designed to fail to demonstrate the issue.
    """
    import litellm

    # Skip this test if no Anthropic API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('No Anthropic API key available')

    # Create a test image and convert it to base64
    test_image = create_test_image()
    screenshot = image_to_png_base64_url(test_image, add_data_prefix=True)

    # Verify the image URL format
    assert screenshot.startswith('data:image/png;base64,'), (
        f"Expected 'data:image/png;base64,' but got {screenshot[:30]}..."
    )

    # Create a message with the screenshot
    formatted_messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': "What's in this image?"},
                {'type': 'image_url', 'image_url': {'url': screenshot}},
            ],
        }
    ]

    # Try to call the Anthropic API directly
    try:
        litellm.completion(
            model='anthropic/claude-3-opus-20240229',
            messages=formatted_messages,
            api_key=api_key,
        )
        # If we get here, the test should fail because no error was raised
        raise AssertionError('Expected BadRequestError was not raised')
    except BadRequestError as e:
        # Verify the error message
        assert 'Image url not in expected format' in str(e), (
            f'Unexpected error message: {str(e)}'
        )

        # This assertion will fail to demonstrate the issue
        assert screenshot.startswith('data:image/jpeg;base64,'), (
            f"Image URL format is incorrect. Expected 'data:image/jpeg;base64,' but got {screenshot[:30]}..."
        )
