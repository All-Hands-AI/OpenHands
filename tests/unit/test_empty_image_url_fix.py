"""Test for fixing empty image URL issue in multimodal browsing."""

from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import ImageContent
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


def test_empty_image_url_handling():
    """Test that empty image URLs are properly filtered out before being sent to LLM."""

    # Create a browser observation with empty screenshot and set_of_marks
    browser_obs = BrowserOutputObservation(
        url='https://example.com',
        trigger_by_action='browse_interactive',
        screenshot='',  # Empty screenshot
        set_of_marks='',  # Empty set_of_marks
        content='Some webpage content',
    )

    # Create conversation memory with vision enabled
    agent_config = AgentConfig(enable_som_visual_browsing=True)
    prompt_manager = PromptManager()
    conv_memory = ConversationMemory(agent_config, prompt_manager)

    # Process the observation with vision enabled
    messages = conv_memory._process_observation(
        obs=browser_obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
        enable_som_visual_browsing=True,
        current_index=0,
        events=[],
    )

    # Check that no empty image URLs are included
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                # All image URLs should be non-empty and valid
                for url in content.image_urls:
                    assert url != '', 'Empty image URL should be filtered out'
                    assert url is not None, 'None image URL should be filtered out'
                    # Should start with data: prefix for base64 images
                    if url:  # Only check if URL is not empty
                        assert url.startswith('data:'), (
                            f'Invalid image URL format: {url}'
                        )


def test_valid_image_url_handling():
    """Test that valid image URLs are properly handled."""

    # Create a browser observation with valid base64 image data
    valid_base64_image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

    browser_obs = BrowserOutputObservation(
        url='https://example.com',
        trigger_by_action='browse_interactive',
        screenshot=valid_base64_image,
        set_of_marks=valid_base64_image,
        content='Some webpage content',
    )

    # Create conversation memory with vision enabled
    agent_config = AgentConfig(enable_som_visual_browsing=True)
    prompt_manager = PromptManager()
    conv_memory = ConversationMemory(agent_config, prompt_manager)

    # Process the observation with vision enabled
    messages = conv_memory._process_observation(
        obs=browser_obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
        enable_som_visual_browsing=True,
        current_index=0,
        events=[],
    )

    # Check that valid image URLs are included
    found_image_content = False
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                found_image_content = True
                # Should have at least one valid image URL
                assert len(content.image_urls) > 0, 'Should have at least one image URL'
                for url in content.image_urls:
                    assert url != '', 'Image URL should not be empty'
                    assert url.startswith('data:image/'), (
                        f'Invalid image URL format: {url}'
                    )

    assert found_image_content, 'Should have found ImageContent with valid URLs'


def test_mixed_image_url_handling():
    """Test handling of mixed valid and invalid image URLs."""

    # Create a browser observation with one empty and one valid image
    valid_base64_image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='

    browser_obs = BrowserOutputObservation(
        url='https://example.com',
        trigger_by_action='browse_interactive',
        screenshot='',  # Empty screenshot
        set_of_marks=valid_base64_image,  # Valid set_of_marks
        content='Some webpage content',
    )

    # Create conversation memory with vision enabled
    agent_config = AgentConfig(enable_som_visual_browsing=True)
    prompt_manager = PromptManager()
    conv_memory = ConversationMemory(agent_config, prompt_manager)

    # Process the observation with vision enabled
    messages = conv_memory._process_observation(
        obs=browser_obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
        enable_som_visual_browsing=True,
        current_index=0,
        events=[],
    )

    # Check that only valid image URLs are included
    found_image_content = False
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                found_image_content = True
                # Should have exactly one valid image URL (set_of_marks)
                assert len(content.image_urls) == 1, (
                    f'Should have exactly one image URL, got {len(content.image_urls)}'
                )
                url = content.image_urls[0]
                assert url == valid_base64_image, (
                    f'Should use the valid image URL: {url}'
                )

    assert found_image_content, 'Should have found ImageContent with valid URL'
