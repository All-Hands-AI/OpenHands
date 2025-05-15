import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.core.schema import AgentState
from openhands.events import EventStream
from openhands.events.action import MessageAction
from openhands.events.event import EventSource
from openhands.llm.metrics import Metrics
from openhands.storage.memory import InMemoryFileStore


# Create separate mock functions so we can track calls
async def mock_process_event(*args, **kwargs):
    print(f'Mock process_single_event_for_mem0 called with: {args[0]}')
    return []


async def mock_webhook_rag(*args, **kwargs):
    print(f'Mock webhook_rag_conversation called with: {args[0]}')
    return True


class DummyAgent:
    def __init__(self):
        self.name = 'dummy'
        self.llm = type(
            'DummyLLM',
            (),
            {
                'metrics': Metrics(),
                'config': type('DummyConfig', (), {'max_message_chars': 10000})(),
            },
        )()

    def reset(self):
        pass


@pytest.mark.asyncio
async def test_iteration_limit_extends_on_user_message():
    # Initialize test components
    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test', file_store=file_store)
    agent = DummyAgent()
    initial_max_iterations = 100

    # Create patches for both async functions
    process_patch = patch(
        'openhands.controller.agent_controller.process_single_event_for_mem0',
        new=AsyncMock(side_effect=mock_process_event),
    )
    webhook_patch = patch(
        'openhands.controller.agent_controller.webhook_rag_conversation',
        new=AsyncMock(side_effect=mock_webhook_rag),
    )

    # Apply both patches
    with process_patch, webhook_patch:
        print('Mocks installed - starting test')
        controller = AgentController(
            agent=agent,
            event_stream=event_stream,
            max_iterations=initial_max_iterations,
            sid='test',
            headless_mode=False,
        )

        # Set initial state
        await controller.set_agent_state_to(AgentState.RUNNING)
        controller.state.iteration = 90  # Close to the limit
        assert controller.state.max_iterations == initial_max_iterations

        # Simulate user message
        user_message = MessageAction('test message', EventSource.USER)
        event_stream.add_event(user_message, EventSource.USER)
        await asyncio.sleep(0.1)  # Give time for event to be processed

        # Verify max_iterations was extended
        assert controller.state.max_iterations == 90 + initial_max_iterations

        # Simulate more iterations and another user message
        controller.state.iteration = 180  # Close to new limit
        user_message2 = MessageAction('another message', EventSource.USER)
        event_stream.add_event(user_message2, EventSource.USER)
        await asyncio.sleep(0.1)  # Give time for event to be processed

        # Verify max_iterations was extended again
        assert controller.state.max_iterations == 180 + initial_max_iterations
