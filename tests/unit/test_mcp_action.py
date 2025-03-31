from unittest import mock

import pytest

from openhands.core.logger import openhands_logger as logger
from openhands.events.action.mcp import McpAction
from openhands.events.observation import Observation
from openhands.runtime.action_execution_server import ActionExecutor


@pytest.mark.asyncio
async def test_mcp_action_execution():
    # Mock the init_user_and_working_directory function to avoid requiring root privileges
    with mock.patch(
        'openhands.runtime.action_execution_server.init_user_and_working_directory',
        return_value=None,
    ):
        # Create a mock ActionExecutor with minimal setup
        executor = ActionExecutor(
            plugins_to_load=[],
            work_dir='/tmp',
            username='test_user',
            user_id=1000,
            browsergym_eval_env=None,
        )

        # Create a McpAction instance
        action = McpAction(mcp_actions='test_action')

        # Execute the action
        observation = await executor.call_tool_mcp(action)
        logger.warning(f'Observation: {observation}')

        # Verify the observation
        assert isinstance(observation, Observation)
        assert 'MCP action received' in observation.content
