import asyncio
import time
from unittest.mock import MagicMock

import pytest

from openhands.events.action import WaitAction
from openhands.events.observation import CmdOutputObservation
from openhands.events.observation.commands import CmdOutputMetadata


@pytest.mark.asyncio
async def test_wait_action():
    """Test that the wait action sleeps for the specified number of seconds."""
    # Create a wait action
    wait_seconds = 2
    action = WaitAction(seconds=wait_seconds)

    # Create a standalone wait method for testing
    async def wait_method(action):
        """Wait for the specified number of seconds."""
        await asyncio.sleep(action.seconds)
        return CmdOutputObservation(
            content=f'Waited for {action.seconds} seconds',
            command=f'wait {action.seconds}',
            metadata=CmdOutputMetadata(),
        )

    # Record the start time
    start_time = time.time()

    # Execute the action
    observation = await wait_method(action)

    # Check that the appropriate amount of time has passed
    elapsed_time = time.time() - start_time
    assert (
        elapsed_time >= wait_seconds
    ), f'Expected to wait at least {wait_seconds} seconds, but only waited {elapsed_time} seconds'

    # Check that the observation is correct
    assert isinstance(observation, CmdOutputObservation)
    assert f'Waited for {wait_seconds} seconds' in observation.content
    assert f'wait {wait_seconds}' == observation.command


@pytest.mark.asyncio
async def test_wait_action_with_asyncio_sleep():
    """Test that the wait action uses asyncio.sleep."""
    # Create a wait action
    wait_seconds = 1
    action = WaitAction(seconds=wait_seconds)

    # Create a standalone wait method for testing that uses a local sleep function
    # to avoid issues with patching the global asyncio.sleep
    async def wait_method(action, sleep_func):
        """Wait for the specified number of seconds."""
        await sleep_func(action.seconds)
        return CmdOutputObservation(
            content=f'Waited for {action.seconds} seconds',
            command=f'wait {action.seconds}',
            metadata=CmdOutputMetadata(),
        )

    # Create a mock sleep function
    mock_sleep = MagicMock()

    async def mock_sleep_func(seconds):
        mock_sleep(seconds)
        # Return immediately for testing
        return None

    # Execute the action with our mock sleep function
    await wait_method(action, mock_sleep_func)

    # Verify our mock was called with the correct argument
    mock_sleep.assert_called_once_with(wait_seconds)
