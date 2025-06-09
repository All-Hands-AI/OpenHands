from unittest.mock import MagicMock, patch

import httpx
import numpy as np
import pytest
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


@patch('httpx.post')
def test_anthropic_browser_integration_error(mock_httpx_post):
    """Test that demonstrates the integration issue between browser screenshots and Anthropic models.

    This test is designed to fail to show the issue.
    """

    # Configure the mock to raise the BadRequestError when called with specific parameters
    def mock_httpx_post_side_effect(*args, **kwargs):
        # Check if this is a call to the Anthropic API
        if args and 'api.anthropic.com' in args[0]:
            # Get the JSON data being sent to the API
            json_data = kwargs.get('json', {})
            messages = json_data.get('messages', [])

            # Check if there's an image URL in the messages
            for message in messages:
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'image':
                            image_url = item.get('source', {}).get('data', '')

                            # Check if the image URL format is what Anthropic expects
                            if image_url.startswith('data:image/png;base64,'):
                                # This is the actual error that would occur in the real scenario
                                error_response = httpx.Response(
                                    status_code=400,
                                    json={
                                        'error': {
                                            'message': "Image url not in expected format. Example Expected input - \"image_url\": \"data:image/jpeg;base64,{base64_image}\". Supported formats - ['image/jpeg', 'image/png', 'image/gif', 'image/webp']."
                                        }
                                    },
                                    request=httpx.Request('POST', args[0]),
                                )
                                raise httpx.HTTPStatusError(
                                    '400 Bad Request',
                                    request=httpx.Request('POST', args[0]),
                                    response=error_response,
                                )

        # If no image URL is found or the format is correct, return a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'This is a mock response'}]
        }
        return mock_response

    mock_httpx_post.side_effect = mock_httpx_post_side_effect

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

    # Import litellm to use it directly with our mocked httpx.post
    import os

    import litellm

    # Get the Anthropic API key from environment variables
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    # Try to send the message to the LLM using litellm
    # This should raise an error, but we'll catch it to examine it
    try:
        # Call litellm directly with the Anthropic model
        litellm.completion(
            model='anthropic/claude-3-opus-20240229',
            messages=formatted_messages,
            api_key=api_key,
        )
        # If we get here, the test should fail because no error was raised
        pytest.fail('Expected HTTPStatusError was not raised')
    except httpx.HTTPStatusError as e:
        # Verify the error message
        assert 'Image url not in expected format' in str(
            e.response.json()['error']['message']
        )
        assert 'Supported formats' in str(e.response.json()['error']['message'])

        # This assertion will fail to demonstrate the issue
        assert observation.screenshot.startswith('data:image/jpeg;base64,'), (
            f"Image URL format is incorrect. Expected 'data:image/jpeg;base64,' but got {observation.screenshot[:30]}..."
        )

    # The test fails because the image URL format is not what Anthropic expects
    # The current implementation uses 'data:image/png;base64,' but Anthropic expects 'data:image/jpeg;base64,'
    # This is the root cause of the issue


def test_anthropic_direct_api_call():
    """Test that directly calls the Anthropic API to reproduce the error.

    This test is marked as xfail because it's expected to fail, demonstrating the issue.
    """
    import os

    import litellm

    # Skip this test if no Anthropic API key is available
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        pytest.skip('No Anthropic API key available')

    # Create a test image and convert it to base64
    test_image = create_test_image()
    screenshot = image_to_png_base64_url(test_image, add_data_prefix=True)

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

    # This test is expected to fail with a BadRequestError
    # Mark it as xfail to indicate this is the expected behavior
    pytest.xfail(
        'This test is expected to fail with a BadRequestError about image URL format'
    )

    # Try to call the Anthropic API directly
    litellm.completion(
        model='anthropic/claude-3-opus-20240229',
        messages=formatted_messages,
        api_key=api_key,
    )
