from unittest.mock import MagicMock

import pytest

from openhands.core.message import ImageContent, TextContent
from openhands.events.observation import IPythonRunCellObservation
from openhands.memory.conversation_memory import ConversationMemory


def test_ipython_observation_with_image_urls():
    """Test that IPythonRunCellObservation correctly handles image_urls."""
    # Create an observation with image URLs
    obs = IPythonRunCellObservation(
        content='Test output',
        code="print('test')",
        image_urls=['data:image/png;base64,abc123'],
    )

    # Check that the image_urls are stored correctly
    assert obs.image_urls == ['data:image/png;base64,abc123']

    # Check that the string representation includes image count
    assert 'Images: 1' in str(obs)


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.enable_som_visual_browsing = False
    config.enable_prompt_extensions = False
    config.disabled_microagents = []
    return config


@pytest.fixture
def mock_prompt_manager():
    return MagicMock()


def test_process_ipython_observation_with_vision_enabled(
    mock_config, mock_prompt_manager
):
    """Test that _process_observation correctly handles IPythonRunCellObservation with image_urls when vision is enabled."""
    # Create a ConversationMemory instance
    memory = ConversationMemory(mock_config, mock_prompt_manager)

    # Create an observation with image URLs
    obs = IPythonRunCellObservation(
        content='Test output',
        code="print('test')",
        image_urls=['data:image/png;base64,abc123'],
    )

    # Process the observation with vision enabled
    messages = memory._process_observation(
        obs=obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=True,
    )

    # Check that the message contains both text and image content
    assert len(messages) == 1
    message = messages[0]
    assert len(message.content) == 2
    assert isinstance(message.content[0], TextContent)
    assert isinstance(message.content[1], ImageContent)
    assert message.content[1].image_urls == ['data:image/png;base64,abc123']


def test_process_ipython_observation_with_vision_disabled(
    mock_config, mock_prompt_manager
):
    """Test that _process_observation correctly handles IPythonRunCellObservation with image_urls when vision is disabled."""
    # Create a ConversationMemory instance
    memory = ConversationMemory(mock_config, mock_prompt_manager)

    # Create an observation with image URLs
    obs = IPythonRunCellObservation(
        content='Test output',
        code="print('test')",
        image_urls=['data:image/png;base64,abc123'],
    )

    # Process the observation with vision disabled
    messages = memory._process_observation(
        obs=obs,
        tool_call_id_to_message={},
        max_message_chars=None,
        vision_is_active=False,
    )

    # Check that the message contains only text content
    assert len(messages) == 1
    message = messages[0]
    assert len(message.content) == 1
    assert isinstance(message.content[0], TextContent)
