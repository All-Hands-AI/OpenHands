"""Test for fixing empty image URL issue in multimodal browsing."""

from openhands.core.config.agent_config import AgentConfig
from openhands.core.message import ImageContent
from openhands.events.observation.browse import BrowserOutputObservation
from openhands.memory.conversation_memory import ConversationMemory
from openhands.utils.prompt import PromptManager


def test_empty_image_url_handling():
    """Test that empty image URLs are properly filtered out and notification text is added."""

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
    prompt_manager = PromptManager(
        prompt_dir='openhands/agenthub/codeact_agent/prompts'
    )
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
    has_image_content = False
    has_notification_text = False
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                has_image_content = True
                # All image URLs should be non-empty and valid
                for url in content.image_urls:
                    assert url != '', 'Empty image URL should be filtered out'
                    assert url is not None, 'None image URL should be filtered out'
                    # Should start with data: prefix for base64 images
                    if url:  # Only check if URL is not empty
                        assert url.startswith('data:'), (
                            f'Invalid image URL format: {url}'
                        )
            elif hasattr(content, 'text'):
                # Check for notification text about missing visual information
                if (
                    'No visual information' in content.text
                    or 'has been filtered' in content.text
                ):
                    has_notification_text = True

    # Should not have image content but should have notification text
    assert not has_image_content, 'Should not have ImageContent for empty images'
    assert has_notification_text, (
        'Should have notification text about missing visual information'
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
    prompt_manager = PromptManager(
        prompt_dir='openhands/agenthub/codeact_agent/prompts'
    )
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
    prompt_manager = PromptManager(
        prompt_dir='openhands/agenthub/codeact_agent/prompts'
    )
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


def test_ipython_empty_image_url_handling():
    """Test that empty image URLs in IPython observations are properly filtered with notification text."""
    from openhands.events.observation.commands import IPythonRunCellObservation

    # Create an IPython observation with empty image URLs
    ipython_obs = IPythonRunCellObservation(
        content='Some output',
        code='print("hello")',
        image_urls=['', None, ''],  # Empty and None image URLs
    )

    # Create conversation memory with vision enabled
    agent_config = AgentConfig(enable_som_visual_browsing=True)
    prompt_manager = PromptManager(
        prompt_dir='openhands/agenthub/codeact_agent/prompts'
    )
    conv_memory = ConversationMemory(agent_config, prompt_manager)

    # Process the observation with vision enabled
    messages = conv_memory._process_observation(
        obs=ipython_obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
        enable_som_visual_browsing=True,
        current_index=0,
        events=[],
    )

    # Check that no empty image URLs are included and notification text is added
    has_image_content = False
    has_notification_text = False
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                has_image_content = True
            elif hasattr(content, 'text'):
                # Check for notification text about filtered images
                if 'invalid or empty and have been filtered' in content.text:
                    has_notification_text = True

    # Should not have image content but should have notification text
    assert not has_image_content, 'Should not have ImageContent for empty images'
    assert has_notification_text, 'Should have notification text about filtered images'


def test_ipython_mixed_image_url_handling():
    """Test handling of mixed valid and invalid image URLs in IPython observations."""
    from openhands.events.observation.commands import IPythonRunCellObservation

    # Create an IPython observation with mixed image URLs
    valid_base64_image = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    ipython_obs = IPythonRunCellObservation(
        content='Some output',
        code='print("hello")',
        image_urls=['', valid_base64_image, None],  # Mix of empty, valid, and None
    )

    # Create conversation memory with vision enabled
    agent_config = AgentConfig(enable_som_visual_browsing=True)
    prompt_manager = PromptManager(
        prompt_dir='openhands/agenthub/codeact_agent/prompts'
    )
    conv_memory = ConversationMemory(agent_config, prompt_manager)

    # Process the observation with vision enabled
    messages = conv_memory._process_observation(
        obs=ipython_obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
        enable_som_visual_browsing=True,
        current_index=0,
        events=[],
    )

    # Check that only valid image URLs are included and notification text is added
    found_image_content = False
    has_notification_text = False
    for message in messages:
        for content in message.content:
            if isinstance(content, ImageContent):
                found_image_content = True
                # Should have exactly one valid image URL
                assert len(content.image_urls) == 1, (
                    f'Should have exactly one image URL, got {len(content.image_urls)}'
                )
                url = content.image_urls[0]
                assert url == valid_base64_image, (
                    f'Should use the valid image URL: {url}'
                )
            elif hasattr(content, 'text'):
                # Check for notification text about filtered images
                if 'invalid or empty image(s) were filtered' in content.text:
                    has_notification_text = True

    assert found_image_content, 'Should have found ImageContent with valid URL'
    assert has_notification_text, 'Should have notification text about filtered images'
