#!/usr/bin/env python3
"""Test script to verify that agent settings are properly applied to the agent configuration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from openhands.core.config import OpenHandsConfig
from openhands.storage.data_models.settings import Settings
from openhands.server.session.session import Session
from openhands.storage.memory import InMemoryFileStore


async def test_agent_settings_application():
    """Test that agent settings from Settings are applied to the agent config."""
    print("Testing agent settings application...")

    # Create a session with a mock config
    config = OpenHandsConfig()
    file_store = InMemoryFileStore({})
    session = Session(
        sid='test-session',
        config=config,
        file_store=file_store,
        sio=None,
        user_id='test-user'
    )

    # Create settings with specific agent configurations
    settings = Settings(
        language='en',
        agent='CodeActAgent',
        enable_llm_editor=True,  # This should enable LLM editor
        enable_editor=False,     # This should disable string editor
        enable_browsing=True,
        enable_jupyter=False,
        enable_cmd=True,
        enable_think=True,
        enable_finish=True,
        enable_prompt_extensions=False,
        disabled_microagents=['github', 'lint'],
        enable_history_truncation=True
    )

    # Mock all the heavy dependencies
    with patch('openhands.controller.agent.Agent.get_cls') as mock_get_cls, \
         patch.object(session, 'agent_session') as mock_agent_session, \
         patch.object(session, '_create_llm') as mock_create_llm:

        # Mock agent class
        mock_agent_class = MagicMock()
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_get_cls.return_value = mock_agent_class

        # Mock LLM
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm

        # Mock agent session start
        mock_agent_session.start = AsyncMock()

        # Call the initialize_agent method
        await session.initialize_agent(settings, initial_message=None, replay_json=None)

        # Check that the agent config was updated in the session's config
        agent_config = config.get_agent_config('CodeActAgent')

        print(f"enable_llm_editor: {agent_config.enable_llm_editor}")
        print(f"enable_editor: {agent_config.enable_editor}")
        print(f"enable_browsing: {agent_config.enable_browsing}")
        print(f"enable_jupyter: {agent_config.enable_jupyter}")
        print(f"enable_cmd: {agent_config.enable_cmd}")
        print(f"enable_think: {agent_config.enable_think}")
        print(f"enable_finish: {agent_config.enable_finish}")
        print(f"enable_prompt_extensions: {agent_config.enable_prompt_extensions}")
        print(f"disabled_microagents: {agent_config.disabled_microagents}")
        print(f"enable_history_truncation: {agent_config.enable_history_truncation}")

        # Verify the settings were applied
        assert agent_config.enable_llm_editor == True, f"Expected enable_llm_editor=True, got {agent_config.enable_llm_editor}"
        assert agent_config.enable_editor == False, f"Expected enable_editor=False, got {agent_config.enable_editor}"
        assert agent_config.enable_browsing == True, f"Expected enable_browsing=True, got {agent_config.enable_browsing}"
        assert agent_config.enable_jupyter == False, f"Expected enable_jupyter=False, got {agent_config.enable_jupyter}"
        assert agent_config.enable_cmd == True, f"Expected enable_cmd=True, got {agent_config.enable_cmd}"
        assert agent_config.enable_think == True, f"Expected enable_think=True, got {agent_config.enable_think}"
        assert agent_config.enable_finish == True, f"Expected enable_finish=True, got {agent_config.enable_finish}"
        assert agent_config.enable_prompt_extensions == False, f"Expected enable_prompt_extensions=False, got {agent_config.enable_prompt_extensions}"
        assert agent_config.disabled_microagents == ['github', 'lint'], f"Expected disabled_microagents=['github', 'lint'], got {agent_config.disabled_microagents}"
        assert agent_config.enable_history_truncation == True, f"Expected enable_history_truncation=True, got {agent_config.enable_history_truncation}"

        print("✅ All agent settings were correctly applied!")

        return True


if __name__ == "__main__":
    asyncio.run(test_agent_settings_application())
