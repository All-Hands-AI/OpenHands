from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from litellm.exceptions import BadRequestError
from PIL import Image

from openhands.core.message import ImageContent, Message, TextContent
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.runtime.browser.base64 import image_to_png_base64_url


def create_test_image():
    """Create a simple test image."""
    # Create a simple 10x10 RGB image
    img_array = np.zeros((10, 10, 3), dtype=np.uint8)
    img_array[:, :, 0] = 255  # Red channel
    return Image.fromarray(img_array)


@patch('litellm.completion')
def test_anthropic_browser_integration_error(mock_completion):
    """Test that demonstrates the integration issue between browser screenshots and Anthropic models.

    This test is designed to fail to show the issue.
    """

    # Configure the mock to raise the BadRequestError when called with specific parameters
    def mock_completion_side_effect(*args, **kwargs):
        messages = kwargs.get('messages', [])

        # Check if there's an image URL in the messages
        for message in messages:
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'image_url':
                        image_url = item.get('image_url', {}).get('url', '')

                        # Check if the image URL format is what Anthropic expects
                        if not image_url.startswith('data:image/jpeg;base64,'):
                            # This is the actual error that would occur in the real scenario
                            raise BadRequestError(
                                message="Error code: 400 - {'error': {'message': 'litellm.BadRequestError: AnthropicException - "
                                'Image url not in expected format. Example Expected input - "image_url": "data:image/jpeg;base64,{base64_image}". '
                                "Supported formats - [\\'image/jpeg\\', \\'image/png\\', \\'image/gif\\', \\'image/webp\\'].",
                                model='claude-3-opus-20240229',
                                llm_provider='anthropic',
                            )

        # If no image URL is found or the format is correct, return a mock response
        return MagicMock()

    mock_completion.side_effect = mock_completion_side_effect

    # Create a test image and convert it to base64
    test_image = create_test_image()
    screenshot = image_to_png_base64_url(test_image, add_data_prefix=True)

    # Create a BrowserOutputObservation with the screenshot
    observation = BrowserOutputObservation(
        content='Test content',
        url='https://example.com',
        screenshot=screenshot,
        trigger_by_action='browse_interactive',
    )

    # Simulate the process of creating a message from the browser observation
    text_content = TextContent(type='text', text=observation.get_agent_obs_text())
    image_content = ImageContent(type='image_url', image_urls=[observation.screenshot])

    # Create a message with both text and image content
    Message(role='user', content=[text_content, image_content], vision_enabled=True)

    # Format the message for the LLM (simplified version of what happens in the real code)
    formatted_messages = [
        {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': observation.get_agent_obs_text()},
                {'type': 'image_url', 'image_url': {'url': observation.screenshot}},
            ],
        }
    ]

    # Try to send the message to the LLM
    # This should raise an error, but we'll catch it to examine it
    try:
        mock_completion(messages=formatted_messages)
        # If we get here, the test should fail because no error was raised
        pytest.fail('Expected BadRequestError was not raised')
    except BadRequestError as e:
        # Verify the error message
        assert 'Image url not in expected format' in str(e)
        assert 'Supported formats' in str(e)

        # This assertion will fail to demonstrate the issue
        assert observation.screenshot.startswith('data:image/jpeg;base64,'), (
            f"Image URL format is incorrect. Expected 'data:image/jpeg;base64,' but got {observation.screenshot[:30]}..."
        )

    # The test fails because the image URL format is not what Anthropic expects
    # The current implementation uses 'data:image/png;base64,' but Anthropic expects 'data:image/jpeg;base64,'
    # This is the root cause of the issue
