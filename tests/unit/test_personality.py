from unittest.mock import MagicMock, patch

import pytest

from openhands.core.message import Message, TextContent
from openhands.microagent import KnowledgeMicroAgent, MicroAgentMetadata, MicroAgentType
from openhands.utils.prompt import PromptManager


@pytest.fixture
def prompt_manager():
    with patch('openhands.utils.prompt.Template') as mock_template, patch.object(
        PromptManager, '_load_template'
    ) as mock_load_template:
        # Mock the render method to return the input
        mock_template_instance = MagicMock()
        mock_template_instance.render.return_value = 'rendered template'
        mock_template.return_value = mock_template_instance
        mock_load_template.return_value = mock_template_instance

        prompt_manager = PromptManager(prompt_dir='/fake/path')

        # Add a mock personality microagent
        personality_microagent = KnowledgeMicroAgent(
            name='enthusiastic_personality',
            content='Be enthusiastic!',
            metadata=MicroAgentMetadata(
                name='enthusiastic_personality', type=MicroAgentType.KNOWLEDGE
            ),
            source='/fake/path/enthusiastic.md',
            type=MicroAgentType.KNOWLEDGE,
        )
        prompt_manager.knowledge_microagents['enthusiastic_personality'] = (
            personality_microagent
        )

        yield prompt_manager


def test_add_info_to_initial_message_with_personality(prompt_manager):
    """Test that personality instructions are added to the initial message."""
    message = Message(role='user', content=[TextContent(text='Hello')])

    # Call the method with a personality
    prompt_manager.add_info_to_initial_message(message, personality='enthusiastic')

    # Check that the personality was passed to the template render method
    render_calls = prompt_manager.additional_info_template.render.call_args_list
    assert len(render_calls) == 1
    render_kwargs = render_calls[0][1]
    assert 'personality_instructions' in render_kwargs
    assert render_kwargs['personality_instructions'] == 'Be enthusiastic!'

    # Check that the rendered template was added to the message
    assert len(message.content) == 2
    assert message.content[0].text == 'rendered template'


def test_add_info_to_initial_message_without_personality(prompt_manager):
    """Test that no personality instructions are added when personality is None."""
    message = Message(role='user', content=[TextContent(text='Hello')])

    # Call the method without a personality
    prompt_manager.add_info_to_initial_message(message, personality=None)

    # Check that an empty string was passed for personality_instructions
    render_calls = prompt_manager.additional_info_template.render.call_args_list
    assert len(render_calls) == 1
    render_kwargs = render_calls[0][1]
    assert 'personality_instructions' in render_kwargs
    assert render_kwargs['personality_instructions'] == ''


def test_add_info_to_initial_message_with_unknown_personality(prompt_manager):
    """Test that no personality instructions are added when personality is unknown."""
    message = Message(role='user', content=[TextContent(text='Hello')])

    # Call the method with an unknown personality
    prompt_manager.add_info_to_initial_message(message, personality='unknown')

    # Check that an empty string was passed for personality_instructions
    render_calls = prompt_manager.additional_info_template.render.call_args_list
    assert len(render_calls) == 1
    render_kwargs = render_calls[0][1]
    assert 'personality_instructions' in render_kwargs
    assert render_kwargs['personality_instructions'] == ''
