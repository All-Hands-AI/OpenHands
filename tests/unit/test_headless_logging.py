import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.events.action import MessageAction
from openhands.events import EventSource, EventStream
from openhands.events.observation import AgentStateChangedObservation
from openhands.core.schema import AgentState
from openhands.runtime.base import Runtime
from openhands.storage.files import FileStore


class MockFileStore(FileStore):
    """Mock file store for testing"""
    def __init__(self):
        self.files = {}

    def read(self, path: str) -> str:
        return self.files.get(path, "")

    def write(self, path: str, contents: str) -> None:
        self.files[path] = contents

    def list(self, path: str) -> list[str]:
        return []

    def delete(self, path: str) -> None:
        if path in self.files:
            del self.files[path]


class MockRuntime(Runtime):
    """Mock runtime for testing"""
    async def connect(self):
        pass

    def run(self, action):
        pass

    def run_ipython(self, action):
        pass

    def read(self, action):
        pass

    def write(self, action):
        pass

    def browse(self, action):
        pass

    def browse_interactive(self, action):
        pass

    def copy_to(self, host_src, sandbox_dest, recursive=False):
        pass

    def list_files(self, path=None):
        return []

    def copy_from(self, path):
        return b""


@pytest.mark.asyncio
async def test_headless_mode_logging():
    # Mock the logger
    mock_logger = MagicMock()
    
    # Create a simple message action
    message = "Test message"
    action = MessageAction(content=message)
    
    # Create a minimal config
    config = AppConfig()
    
    # Create event stream and runtime
    file_store = MockFileStore()
    event_stream = EventStream("test", file_store)
    runtime = MockRuntime(config=config, event_stream=event_stream, sid="test")
    
    # Mock the logger.info method
    with patch("openhands.core.main.logger", mock_logger):
        # Run the controller in headless mode
        await run_controller(
            config=config,
            initial_user_action=action,
            headless_mode=True,
            exit_on_message=True,  # Exit when agent asks for input
            runtime=runtime
        )
        
        # Verify that logger.info was called with events
        assert mock_logger.info.call_count > 0
        
        # Verify that at least one call was with our test message action
        found_message = False
        for call in mock_logger.info.call_args_list:
            args = call[0]
            if isinstance(args[0], MessageAction) and args[0].content == message:
                found_message = True
                break
        assert found_message, "Test message action was not logged"
