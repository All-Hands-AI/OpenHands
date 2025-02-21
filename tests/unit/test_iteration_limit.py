import asyncio

import pytest

from openhands.controller.agent_controller import AgentController
from openhands.core.schema import AgentState
from openhands.events import EventStream
from openhands.events.action import MessageAction
from openhands.events.event import EventSource
from openhands.llm.metrics import Metrics


class DummyAgent:
    def __init__(self):
        self.name = 'dummy'
        self.llm = type(
            'DummyLLM',
            (),
            {
                'metrics': Metrics(),
                'config': type('DummyConfig', (), {'max_message_chars': 1000})(),
            },
        )()

    def reset(self):
        pass


@pytest.mark.asyncio
async def test_iteration_limit_extends_on_user_message():
    # Initialize test components
    from openhands.storage.memory import InMemoryFileStore

    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test', file_store=file_store)
    agent = DummyAgent()
    initial_max_iterations = 100
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


@pytest.mark.asyncio
async def test_iteration_limit_in_headless_mode_with_agent_steps():
    # Initialize test components
    from openhands.storage.memory import InMemoryFileStore
    from openhands.events.action import AgentFinishAction, CmdRunAction

    class SteppingAgent(DummyAgent):
        def step(self, state):
            # Return a command action that will trigger another step
            return CmdRunAction(command="echo test")

    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test', file_store=file_store)
    agent = SteppingAgent()
    initial_max_iterations = 1  # Set to 1 as in the user's config
    controller = AgentController(
        agent=agent,
        event_stream=event_stream,
        max_iterations=initial_max_iterations,
        sid='test',
        headless_mode=True,
    )

    # Set initial state
    await controller.set_agent_state_to(AgentState.RUNNING)
    
    # Trigger the first step
    user_message = MessageAction('start', EventSource.USER)
    event_stream.add_event(user_message, EventSource.USER)
    await asyncio.sleep(0.1)  # Give time for event to be processed
    
    # Record the iteration count
    iteration_count = controller.state.iteration
    
    # Trigger another step by sending the command output
    from openhands.events.observation.commands import CmdOutputObservation
    event_stream.add_event(
        CmdOutputObservation(content="test", command="echo test", exit_code=0),
        EventSource.AGENT,
    )
    await asyncio.sleep(0.1)  # Give time for event to be processed
    
    # The iteration count should not have increased since we hit the limit
    assert controller.state.iteration == iteration_count, \
        f"Agent continued running after hitting max_iterations={initial_max_iterations} (iteration count: {controller.state.iteration})"
    
    # The agent should be in ERROR state
    assert controller.get_agent_state() == AgentState.ERROR, \
        f"Agent should be in ERROR state after hitting max_iterations, but was in {controller.get_agent_state()}"


@pytest.mark.asyncio
async def test_iteration_limit_in_headless_mode():
    # Initialize test components
    from openhands.storage.memory import InMemoryFileStore

    file_store = InMemoryFileStore()
    event_stream = EventStream(sid='test', file_store=file_store)
    agent = DummyAgent()
    initial_max_iterations = 1
    controller = AgentController(
        agent=agent,
        event_stream=event_stream,
        max_iterations=initial_max_iterations,
        sid='test',
        headless_mode=True,
    )

    # Set initial state
    await controller.set_agent_state_to(AgentState.RUNNING)
    controller.state.iteration = 1  # At the limit
    assert controller.state.max_iterations == initial_max_iterations

    # Simulate user message
    user_message = MessageAction('test message', EventSource.USER)
    event_stream.add_event(user_message, EventSource.USER)
    await asyncio.sleep(0.1)  # Give time for event to be processed

    # Verify that the agent stopped at the limit
    assert controller.get_agent_state() == AgentState.ERROR, "Agent should be in ERROR state after hitting max_iterations in headless mode"
