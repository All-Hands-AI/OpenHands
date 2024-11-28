import asyncio
import json
import logging
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhands.controller.agent import Agent
from openhands.core.config import AppConfig
from openhands.core.main import run_controller
from openhands.events import EventStream
from openhands.events.action import MessageAction
from openhands.events.event import Event, EventSource
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM
from openhands.runtime.base import Runtime
from openhands.storage.memory import InMemoryFileStore


class TestAgent(Agent):
    """A test agent class that does nothing."""
    def __init__(self, llm: LLM, config: dict):
        super().__init__(llm, config)

    def step(self, state: 'State') -> 'Action':
        """Simple step implementation that just returns a message action."""
        self._complete = True
        return MessageAction(content="test response")


# Register the test agent
Agent.register("test_agent", TestAgent)


class MockRuntime(Runtime):
    """A mock runtime for testing."""
    def __init__(self, event_stream: EventStream, **kwargs):
        super().__init__(event_stream=event_stream, **kwargs)

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    def run(self, action):
        return None

    def run_ipython(self, action):
        return None

    def read(self, action):
        return None

    def write(self, action):
        return None

    def browse(self, action):
        return None

    def browse_interactive(self, action):
        return None

    def copy_to(self, host_src, sandbox_dest, recursive=False):
        pass

    def list_files(self, path=None):
        return []

    def copy_from(self, path):
        return None


class TestEventStream(EventStream):
    """A test event stream that uses a synchronous version of add_event."""
    def add_event(self, event: Event, source: EventSource):
        if hasattr(event, '_id') and event.id is not None:
            raise ValueError(
                'Event already has an ID. It was probably added back to the EventStream from inside a handler, trigging a loop.'
            )
        with self._lock:
            event._id = self._cur_id  # type: ignore [attr-defined]
            self._cur_id += 1
        event._timestamp = datetime.now().isoformat()
        event._source = source  # type: ignore [attr-defined]
        data = event_to_dict(event)
        if event.id is not None:
            self.file_store.write(self._get_filename_for_id(event.id), json.dumps(data))
        tasks = []
        for key in sorted(self._subscribers.keys()):
            callbacks = self._subscribers[key]
            for callback_id in callbacks:
                callback = callbacks[callback_id]
                tasks.append(callback(event))
        if tasks:
            # Create a new event loop if there isn't one
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            # Run all tasks in the event loop
            loop.run_until_complete(asyncio.gather(*tasks))


@pytest.mark.asyncio
async def test_headless_mode_logging():
    # Mock logger
    mock_logger = MagicMock()
    
    # Mock config
    config = AppConfig()
    config.default_agent = "test_agent"
    config.file_store = "memory"
    config.max_iterations = 1
    config.max_budget_per_task = 1.0
    
    # Create a simple message action
    initial_action = MessageAction(content="test task")
    
    # Create a mock runtime with unique session ID
    file_store = InMemoryFileStore()
    session_id = str(uuid.uuid4())
    event_stream = TestEventStream(session_id, file_store)
    runtime = MockRuntime(event_stream=event_stream, config=config)
    
    # Mock asyncio.sleep to avoid delays
    async def mock_sleep(*args, **kwargs):
        pass

    # Mock the logger.info method and shutdown listener
    with patch("openhands.core.main.logger", mock_logger), \
         patch("openhands.utils.shutdown_listener._register_signal_handlers"), \
         patch("openhands.utils.shutdown_listener.should_continue", return_value=False), \
         patch("asyncio.sleep", mock_sleep):
        # Run controller in headless mode
        await run_controller(
            config=config,
            initial_user_action=initial_action,
            exit_on_message=True,
            headless_mode=True,
            runtime=runtime,
            sid=session_id
        )
        
        # Verify that logger.info was called with Event objects
        info_calls = mock_logger.info.call_args_list
        assert len(info_calls) > 0
        for call in info_calls:
            args = call[0]
            assert isinstance(args[0], Event)

        # Run controller with headless_mode=False
        mock_logger.reset_mock()
        session_id = str(uuid.uuid4())
        event_stream = TestEventStream(session_id, file_store)
        runtime = MockRuntime(event_stream=event_stream, config=config)
        await run_controller(
            config=config,
            initial_user_action=initial_action,
            exit_on_message=True,
            headless_mode=False,
            runtime=runtime,
            sid=session_id
        )
        
        # Verify logger.info was not called when headless_mode=False
        assert mock_logger.info.call_count == 0
