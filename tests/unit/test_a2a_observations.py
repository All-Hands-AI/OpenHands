from datetime import datetime
from typing import Any, Literal

import pytest
from pydantic import BaseModel

from openhands.a2a.common.types import (
    Artifact,
    Message,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from openhands.core.schema import ObservationType
from openhands.events.observation.a2a import (
    A2ASendTaskArtifactObservation,
    A2ASendTaskResponseObservation,
    A2ASendTaskUpdateObservation,
)
from openhands.events.serialization.event import event_from_dict, event_to_dict


# Deep nested models for testing
class AgentMetadata(BaseModel):
    name: str
    version: str
    capabilities: list[str]


class AgentInfo(BaseModel):
    id: str
    metadata: AgentMetadata
    status: str
    last_active: datetime


class RemoteAgentsList(BaseModel):
    agents: list[AgentInfo]
    total_count: int
    active_count: int


class TaskPart(BaseModel):
    content: str
    role: Literal['user', 'agent']
    metadata: dict[str, Any] | None = None


class TaskMetadata(BaseModel):
    priority: int
    tags: list[str]
    custom_data: dict[str, Any] | None = None


class DeepTaskStatus(BaseModel):
    state: str
    progress: float
    error: str | None = None
    metadata: TaskMetadata | None = None


class DeepTaskArtifact(BaseModel):
    name: str
    content: str
    parts: list[TaskPart]
    metadata: TaskMetadata | None = None


class DeepTask(BaseModel):
    id: str
    session_id: str | None = None
    final: bool = False
    metadata: TaskMetadata | None = None
    content: str
    parts: list[TaskPart]


@pytest.mark.skip(reason='List remote agents observation needs further investigation')
def test_a2a_list_remote_agents_observation():
    # This test is skipped for now as it needs further investigation
    # regarding how to properly structure the A2AListRemoteAgentsObservation
    # for serialization to include remote_agents in the extras
    pass


def test_a2a_send_task_update_observation():
    # Create test data based on the actual required TaskStatus model
    text_part = TextPart(
        text='Test update message', metadata={'timestamp': '2024-03-20T10:00:00'}
    )

    message = Message(role='agent', parts=[text_part], metadata={'confidence': 0.9})

    task_status = TaskStatus(
        state=TaskState.WORKING,  # Use the enum value
        message=message,
    )

    task_update_event = TaskStatusUpdateEvent(
        id='task123',
        status=task_status,
        final=False,
        metadata={
            'priority': 1,
            'tags': ['test', 'update'],
            'custom_data': {'key': 'value'},
        },
    )

    # Create with required content parameter
    event = A2ASendTaskUpdateObservation(
        content='Task update event',
        task_update_event=task_update_event,
        agent_name='test_agent',
    )
    event._id = 456  # Set ID explicitly for test

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 456
    assert event_dict['observation'] == ObservationType.A2A_SEND_TASK_UPDATE_EVENT
    assert event_dict['extras']['task_update_event']['id'] == 'task123'
    assert event_dict['extras']['task_update_event']['status']['state'] == 'working'

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 456
    assert deserialized_event.observation == ObservationType.A2A_SEND_TASK_UPDATE_EVENT
    assert isinstance(deserialized_event.task_update_event, dict)
    assert deserialized_event.task_update_event['id'] == 'task123'
    assert deserialized_event.task_update_event['status']['state'] == 'working'


def test_a2a_send_task_artifact_observation():
    # Create test data based on the actual Artifact model
    text_part = TextPart(text='Test artifact content', metadata={'confidence': 0.9})

    artifact = Artifact(
        name='test_artifact',
        description='Test artifact description',
        parts=[text_part],
        metadata={
            'priority': 2,
            'tags': ['test', 'artifact'],
            'custom_data': {'type': 'code'},
        },
    )

    task_artifact_event = TaskArtifactUpdateEvent(id='task789', artifact=artifact)

    # Create with required content parameter
    event = A2ASendTaskArtifactObservation(
        content='Task artifact event',
        task_artifact_event=task_artifact_event,
        agent_name='test_agent',
    )
    event._id = 789  # Set ID explicitly for test

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 789
    assert event_dict['observation'] == ObservationType.A2A_SEND_TASK_ARTIFACT
    assert event_dict['extras']['task_artifact_event']['id'] == 'task789'
    assert (
        event_dict['extras']['task_artifact_event']['artifact']['name']
        == 'test_artifact'
    )

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 789
    assert deserialized_event.observation == ObservationType.A2A_SEND_TASK_ARTIFACT
    assert isinstance(deserialized_event.task_artifact_event, dict)
    assert deserialized_event.task_artifact_event['id'] == 'task789'
    assert deserialized_event.task_artifact_event['artifact']['name'] == 'test_artifact'


def test_a2a_send_task_response_observation():
    # Create test data based on the actual Task model
    text_part1 = TextPart(
        text="What's the weather?", metadata={'timestamp': '2024-03-20T10:00:00'}
    )

    text_part2 = TextPart(text='The weather is sunny!', metadata={'confidence': 0.95})

    message = Message(role='agent', parts=[text_part1, text_part2], metadata={})

    task_status = TaskStatus(state=TaskState.COMPLETED, message=message)

    task = Task(
        id='task123',
        sessionId='session456',
        status=task_status,
        metadata={
            'priority': 3,
            'tags': ['test', 'response'],
            'custom_data': {'status': 'completed'},
        },
    )

    # Create with required content parameter
    event = A2ASendTaskResponseObservation(
        content='Task response received', task=task, agent_name='test_agent'
    )
    event._id = 999  # Set ID explicitly for test

    # Test serialization
    event_dict = event_to_dict(event)
    assert event_dict['id'] == 999
    assert event_dict['observation'] == ObservationType.A2A_SEND_TASK_RESPONSE
    assert event_dict['extras']['task']['id'] == 'task123'
    assert event_dict['extras']['task']['sessionId'] == 'session456'
    assert event_dict['extras']['task']['status']['state'] == 'completed'

    # Test deserialization
    deserialized_event = event_from_dict(event_dict)
    assert deserialized_event._id == 999
    assert deserialized_event.observation == ObservationType.A2A_SEND_TASK_RESPONSE
    assert isinstance(deserialized_event.task, dict)
    assert deserialized_event.task['id'] == 'task123'
    assert deserialized_event.task['sessionId'] == 'session456'
    assert deserialized_event.task['status']['state'] == 'completed'
    assert deserialized_event.task['metadata']['custom_data']['status'] == 'completed'
