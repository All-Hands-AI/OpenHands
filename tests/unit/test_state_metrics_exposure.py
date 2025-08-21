import asyncio
from unittest.mock import patch

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events.action import MessageAction
from openhands.llm.metrics import Metrics


class FakeEventStream:
    def __init__(self):
        self.sid = 'test-sid'
        self.file_store = None
        self.user_id = None

    def add_event(self, *args, **kwargs):
        pass

    def subscribe(self, *args, **kwargs):
        pass

    def close(self):
        pass


class FakeRuntime:
    def __init__(self):
        self.event_stream = FakeEventStream()

    async def connect(self):
        return None

    def close(self):
        pass


class DummyState:
    def __init__(self, conversation_stats):
        self.conversation_stats = conversation_stats
        self.metrics = Metrics()
        self.history = []
        self.last_error = ''
        self.extra_data = {}


class FakeController:
    def __init__(self, state):
        self._state = state

    def get_state(self):
        return self._state

    async def close(self, set_stop_state: bool = False):
        return None

    def get_trajectory(self, include_screenshots: bool = False):
        return []


class FakeConversationStats:
    def __init__(self, cost: float = 1.23):
        self._m = Metrics()
        self._m.add_cost(cost)

    def get_combined_metrics(self) -> Metrics:
        return self._m


def test_state_tracker_save_state_consolidates_metrics(tmp_path):
    """Ensure StateTracker.save_state persists ConversationStats and does not touch State.metrics.

    Eval scripts should read from state.conversation_stats via evaluation.utils.shared.get_metrics.
    """
    from openhands.controller.state.state_tracker import StateTracker
    from openhands.server.services.conversation_stats import ConversationStats
    from openhands.storage.memory import InMemoryFileStore

    # Prepare conversation stats with one service metrics
    store = InMemoryFileStore({})
    conv_stats = ConversationStats(
        file_store=store, conversation_id='cid', user_id=None
    )
    m = Metrics()
    m.add_cost(0.5)
    conv_stats.service_to_metrics['svc'] = m

    # Create a new tracker and initialize state
    tracker = StateTracker(sid='sid', file_store=store, user_id=None)
    tracker.set_initial_state(
        id='sid',
        state=None,
        conversation_stats=conv_stats,
        max_iterations=1,
        max_budget_per_task=None,
        confirmation_mode=False,
    )

    # Preconditions
    assert tracker.state.metrics.accumulated_cost == 0.0

    # Act
    tracker.save_state()

    # Assert state.metrics unaffected (source of truth remains ConversationStats)
    assert tracker.state.metrics.accumulated_cost == 0.0
    # Persistence still called on ConversationStats (no exception)


def test_run_controller_exposes_aggregated_metrics_in_state():
    """Ensure get_metrics(state) reads from ConversationStats when available."""
    from evaluation.utils.shared import get_metrics
    from openhands.core.main import run_controller

    cfg = OpenHandsConfig()
    # Prevent run_controller from trying to persist state via DummyState
    cfg.file_store = 'memory'

    fake_conv_stats = FakeConversationStats(cost=2.5)

    def fake_create_registry_and_conversation_stats(config, sid, _):
        # return (llm_registry, conversation_stats, config)
        return (None, fake_conv_stats, config)

    def fake_create_agent(config, llm_registry):
        class _AgentCfg:
            enable_mcp = False

        class _LLMCfg:
            model = 'test-model'

        class _LLM:
            config = _LLMCfg()

        class _Agent:
            name = 'FakeAgent'
            config = _AgentCfg()
            llm = _LLM()

        return _Agent()

    def fake_create_runtime(
        config,
        llm_registry,
        sid=None,
        headless_mode=True,
        agent=None,
        git_provider_tokens=None,
    ):
        return FakeRuntime()

    def fake_create_memory(
        runtime,
        event_stream,
        sid,
        selected_repository=None,
        repo_directory=None,
        status_callback=None,
        conversation_instructions=None,
        working_dir=None,
    ):
        return object()

    def fake_create_controller(
        agent,
        runtime,
        config,
        conversation_stats,
        headless_mode=True,
        replay_events=None,
    ):
        # Return a controller that yields a DummyState with provided conversation_stats
        state = DummyState(conversation_stats)
        return (FakeController(state), None)

    # Invoke run_controller under patch context
    with (
        patch(
            'openhands.core.main.create_registry_and_conversation_stats',
            side_effect=fake_create_registry_and_conversation_stats,
        ),
        patch('openhands.core.main.create_agent', side_effect=fake_create_agent),
        patch('openhands.core.main.create_runtime', side_effect=fake_create_runtime),
        patch('openhands.core.main.create_memory', side_effect=fake_create_memory),
        patch(
            'openhands.core.main.create_controller', side_effect=fake_create_controller
        ),
        patch(
            'openhands.core.main.run_agent_until_done',
            side_effect=lambda *args, **kwargs: None,
        ),
    ):
        state = asyncio.run(
            run_controller(
                config=cfg,
                initial_user_action=MessageAction(content='hi'),
                sid='sid',
                fake_user_response_fn=None,
            )
        )

    assert state is not None
    # get_metrics must prefer conversation_stats and reflect its values
    m = get_metrics(state)
    assert pytest.approx(m.get('accumulated_cost', 0.0), rel=1e-6) == 2.5
