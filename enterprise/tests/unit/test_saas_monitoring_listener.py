import pytest
from server.saas_monitoring_listener import SaaSMonitoringListener

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.schema.agent import AgentState
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
)


@pytest.fixture
def listener():
    return SaaSMonitoringListener.get_instance(OpenHandsConfig())


def test_on_session_event_with_agent_state_changed_non_error(listener):
    event = AgentStateChangedObservation('', AgentState.STOPPED)

    listener.on_session_event(event)


def test_on_session_event_with_agent_state_changed_error(listener):
    event = AgentStateChangedObservation('', AgentState.ERROR)

    listener.on_session_event(event)


def test_on_session_event_with_other_event(listener):
    listener.on_session_event(Event())


def test_on_agent_session_start_success(listener):
    listener.on_agent_session_start(success=True, duration=1.5)


def test_on_agent_session_start_failure(listener):
    listener.on_agent_session_start(success=False, duration=0.5)


def test_on_create_conversation(listener):
    listener.on_create_conversation()
