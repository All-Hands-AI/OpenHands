import types
from types import MappingProxyType, SimpleNamespace
from typing import Any, Literal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from a2a.types import (
    Message,
    MessageSendParams,
    SendMessageRequest,
    Task,
    TaskIdParams,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskQueryParams,
    TaskState,
    TaskStatus,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import (
    ServerError,
)
from pydantic import BaseModel

from openhands.core.schema.agent import AgentState
from openhands.events.action import MessageAction, NullAction
from openhands.events.event import EventSource
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.server.a2a.a2a_request_handler import A2aRequestHandler


@pytest.mark.asyncio
async def test_on_get_task(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'taskid123'
    params = TaskQueryParams(id=task_id)

    A2aRequestHandler._task_id_to_sessions[task_id] = MagicMock()

    async def mock_create_a2a_response(self, task_id, params):
        return Task(
            id=task_id,
            contextId=task_id,
            status=TaskStatus(state=TaskState.working),
            history=[],
            kind='task',
        )

    monkeypatch.setattr(
        A2aRequestHandler,
        '_create_a2a_response',
        mock_create_a2a_response,
    )

    result = await handler.on_get_task(params, MagicMock())

    assert result.status.state == TaskState.working


@pytest.mark.asyncio
async def test_on_get_task_notfound(monkeypatch):
    handler = A2aRequestHandler()
    mock_params = TaskQueryParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_get_task(mock_params, MagicMock())

    assert isinstance(exc_info.value.error, TaskNotFoundError)


@pytest.mark.asyncio
async def test_on_cancel_task(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'taskid123'
    params = TaskIdParams(id=task_id)

    mock_session = MagicMock()
    mock_session.dispatch = AsyncMock(return_value=None)
    A2aRequestHandler._task_id_to_sessions = {task_id: mock_session}

    async def mock_create_a2a_response(self, task_id, params):
        return Task(
            id=task_id,
            contextId=task_id,
            status=TaskStatus(state=TaskState.canceled),
            history=[],
            kind='task',
        )

    monkeypatch.setattr(
        A2aRequestHandler,
        '_create_a2a_response',
        mock_create_a2a_response,
    )

    result = await handler.on_cancel_task(params, MagicMock())

    assert result.status.state == TaskState.canceled


@pytest.mark.asyncio
async def test_on_cancel_task_notfound(monkeypatch):
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_cancel_task(mock_params, MagicMock())

    assert isinstance(exc_info.value.error, TaskNotFoundError)


@pytest.mark.asyncio
async def test_on_message_send(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'taskid123'
    params = ReqParams().send_id()

    mock_session = AsyncMock()
    mock_session.initialize_agent = AsyncMock()
    mock_session.dispatch = AsyncMock()

    A2aRequestHandler._task_id_to_sessions = {task_id: mock_session}

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.Session',
        lambda **kwargs: mock_session,
    )

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._conversation_init_data_set',
        AsyncMock(return_value={'agent': 'CodeActAgent'}),
    )

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._convert_a2a_params_to_dict',
        lambda _: {'action': 'message', 'args': {'content': 'hello'}, 'source': 'user'},
    )

    result = await handler.on_message_send(params, MagicMock())

    assert isinstance(result, Task)
    assert result.id == task_id
    assert result.status.state == TaskState.working


@pytest.mark.asyncio
async def test_on_message_send_new(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'taskid123'
    params = ReqParams().send_id()

    mock_session = AsyncMock()
    mock_session.initialize_agent = AsyncMock()
    mock_session.dispatch = AsyncMock()

    A2aRequestHandler._task_id_to_sessions = {}

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.Session',
        lambda **kwargs: mock_session,
    )

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._conversation_init_data_set',
        AsyncMock(return_value={'agent': 'CodeActAgent'}),
    )

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._convert_a2a_params_to_dict',
        lambda _: {
            'action': 'message',
            'args': {'content': 'hello'},
            'source': EventSource.USER,
        },
    )

    result = await handler.on_message_send(params, MagicMock())

    assert isinstance(result, Task)
    assert result.id == task_id
    assert result.status.state == TaskState.working


def test__convert_a2a_params_to_dict_message_send():
    msg = Message(
        role='user',
        parts=[{'kind': 'text', 'text': 'hello'}],
        messageId=uuid4().hex,
        taskId=uuid4().hex,
        kind='message',
    )
    params = MessageSendParams(message=msg)
    handler = A2aRequestHandler()
    result = handler._convert_a2a_params_to_dict(params)

    assert result['action'] == 'message'
    assert result['args']['content'] == 'hello'
    assert result['source'] == EventSource.USER


def test__convert_a2a_params_to_dict_query():
    params = TaskQueryParams(id='dummy-task')
    handler = A2aRequestHandler()
    result = handler._convert_a2a_params_to_dict(params)

    assert result['action'] == 'change_agent_state'
    assert result['args']['agent_state'] == 'stopped'
    assert result['source'] == EventSource.USER


def test__convert_a2a_params_to_dict():
    params = TaskIdParams(id='dummy-task')
    handler = A2aRequestHandler()
    result = handler._convert_a2a_params_to_dict(params)

    assert result['action'] == 'change_agent_state'
    assert result['args']['agent_state'] == 'stopped'
    assert result['source'] == EventSource.USER


def test__convert_a2a_params_to_dic_invalid_type():
    class Dummy:
        pass

    handler = A2aRequestHandler()
    with pytest.raises(ServerError) as e:
        handler._convert_a2a_params_to_dict(Dummy())
    assert isinstance(e.value.error, UnsupportedOperationError)


def test__params_get_task_id_message():
    task_id = 'taskid123'
    params = ReqParams().send_id()

    handler = A2aRequestHandler()
    result = handler._params_get_task_id(params)

    assert result == task_id


def test__params_get_task_id_message_noid():
    task_id = 'taskid123'
    params = ReqParams().send_notid()

    handler = A2aRequestHandler()
    result = handler._params_get_task_id(params)

    assert result != task_id


def test__params_get_task_id_get():
    params = TaskQueryParams(id='tid')

    handler = A2aRequestHandler()
    response = handler._params_get_task_id(params)
    assert response == 'tid'


def test__params_get_task_id_cancel():
    params = TaskIdParams(id='tid')

    handler = A2aRequestHandler()
    response = handler._params_get_task_id(params)
    assert response == 'tid'


def test__params_get_task_id_unsupport():
    handler = A2aRequestHandler()
    params = ReqParams().unsupported()
    with pytest.raises(ServerError) as exc_info:
        handler._params_get_task_id(params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


def test__server_preparation():
    params = ReqParams().send_id()

    handler = A2aRequestHandler()

    task_id = 'taskid123'

    result = handler._server_preparation(task_id, params)

    assert result.id == 'taskid123'


@pytest.mark.asyncio
async def test__conversation_init_data_set_raise(monkeypatch):
    handler = A2aRequestHandler()

    params = ReqParams().send_id()
    params.metadata = {'agent': 'CodeActAgent'}

    settings_instance = AsyncMock()
    settings_instance.load = AsyncMock(return_value=None)
    monkeypatch.setattr(
        'openhands.server.shared.SettingsStoreImpl.get_instance',
        AsyncMock(return_value=settings_instance),
    )

    secrets = SimpleNamespace(
        provider_tokens=MappingProxyType({'gh': 'tok'}),
        custom_secrets=MappingProxyType({'x': 'y'}),
    )
    secrets_instance = AsyncMock()
    secrets_instance.load = AsyncMock(return_value=secrets)
    monkeypatch.setattr(
        'openhands.server.shared.SecretsStoreImpl.get_instance',
        AsyncMock(return_value=secrets_instance),
    )

    monkeypatch.setattr(
        'openhands.server.shared.server_config', SimpleNamespace(app_mode='local')
    )

    with pytest.raises(ConnectionRefusedError) as exc_info:
        await handler._conversation_init_data_set(params)

    assert 'Settings not found' in str(exc_info.value)


@pytest.mark.asyncio
async def test__conversation_init_data_set(monkeypatch):
    handler = A2aRequestHandler()

    params = TaskQueryParams(id='tid')
    handler._params_get_task_id(params)

    settings = SimpleNamespace(s1='v1')
    settings_instance = AsyncMock()
    settings_instance.load = AsyncMock(return_value=settings)

    monkeypatch.setattr(
        'openhands.server.shared.SettingsStoreImpl.get_instance',
        AsyncMock(return_value=settings_instance),
    )

    secrets = SimpleNamespace(
        provider_tokens=MappingProxyType({'gh': 'tok'}),
        custom_secrets=MappingProxyType({'x': 'y'}),
    )
    secrets_instance = AsyncMock()
    secrets_instance.load = AsyncMock(return_value=secrets)

    monkeypatch.setattr(
        'openhands.server.shared.SecretsStoreImpl.get_instance',
        AsyncMock(return_value=secrets_instance),
    )

    monkeypatch.setattr(
        'openhands.server.shared.server_config', SimpleNamespace(app_mode='local')
    )

    params = ReqParams().send_id()
    params.metadata = {'agent': 'CodeActAgent'}

    result = await handler._conversation_init_data_set(params)

    assert result.agent == 'CodeActAgent'


@pytest.mark.asyncio
async def test_on_message_send_stream():
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_message_send_stream(mock_params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


@pytest.mark.asyncio
async def test_on_set_task_push_notification_config():
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_set_task_push_notification_config(mock_params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


@pytest.mark.asyncio
async def test_on_get_task_push_notification_config():
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_get_task_push_notification_config(mock_params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


@pytest.mark.asyncio
async def test_on_resubscribe_to_task():
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        await handler.on_resubscribe_to_task(mock_params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


def test_should_add_push_info():
    handler = A2aRequestHandler()
    mock_params = TaskIdParams(id='test-task-id')
    with pytest.raises(ServerError) as exc_info:
        handler.should_add_push_info(mock_params)

    assert isinstance(exc_info.value.error, UnsupportedOperationError)


@pytest.mark.asyncio
async def test__background_task(monkeypatch):
    handler = A2aRequestHandler()
    session = AsyncMock()
    conversation_init_data = {'agent': 'CodeActAgent'}
    task_id = 'taskid123'

    class DummyMessage:
        def __init__(self):
            self.messageId = ''

    class DummyParams:
        def __init__(self):
            self.message = DummyMessage()

    params = DummyParams()

    agent_event = MagicMock(spec=AgentStateChangedObservation)
    agent_event.source = EventSource.AGENT
    agent_event.id = 1
    agent_event.agent_state = 'working'

    user_event = MagicMock(spec=AgentStateChangedObservation)
    user_event.source = EventSource.USER
    user_event.id = 2
    user_event.agent_state = 'working'

    skip_event = MagicMock(spec=NullAction)

    all_events = [skip_event, agent_event, user_event]

    class MockAsyncEventStore:
        def __aiter__(self):
            async def generator():
                for event in all_events:
                    yield event

            return generator()

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._convert_a2a_params_to_dict',
        lambda self, _: {
            'action': 'message',
            'args': {'content': 'hello'},
            'source': 'user',
        },
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda tid, store, user_id=None: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: MockAsyncEventStore(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    await handler._background_task(session, conversation_init_data, params, task_id)

    session.initialize_agent.assert_awaited_once_with(
        conversation_init_data, None, replay_json=None
    )
    session.dispatch.assert_awaited_once()
    assert handler._task_id_to_sessions[task_id] == session

    assert (task_id, agent_event.id) in handler._message_to_task_event
    assert (task_id, user_event.id) in handler._message_to_task_event
    assert isinstance(handler._message_to_task_event[(task_id, agent_event.id)], str)
    assert isinstance(handler._message_to_task_event[(task_id, user_event.id)], str)


@pytest.mark.asyncio
async def test__background_task_session_already_exists(monkeypatch):
    handler = A2aRequestHandler()
    session = AsyncMock()
    conversation_init_data = {'agent': 'CodeActAgent'}
    task_id = 'taskid123'
    params = ReqParams().send_id()

    handler._task_id_to_sessions = {task_id: session}

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.A2aRequestHandler._convert_a2a_params_to_dict',
        lambda self, _: {
            'action': 'message',
            'args': {'content': 'hello'},
            'source': 'user',
        },
    )

    await handler._background_task(session, conversation_init_data, params, task_id)

    session.initialize_agent.assert_not_awaited()
    session.dispatch.assert_awaited_once()
    assert handler._task_id_to_sessions[task_id] == session


@pytest.mark.asyncio
async def test__create_a2a_response_completed(monkeypatch):
    handler = A2aRequestHandler()
    params = TaskQueryParams(id='tid')

    event = MagicMock(spec=AgentStateChangedObservation)
    event.source = EventSource.AGENT
    event.message = 'Task finished'
    event.agent_state = AgentState.FINISHED

    async def mock_async_iter():
        yield event

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: mock_async_iter(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    task = await handler._create_a2a_response('tid', params)
    assert isinstance(task, Task)
    assert task.status.state == TaskState.completed


@pytest.mark.asyncio
async def test__create_a2a_response_canceled(monkeypatch):
    handler = A2aRequestHandler()
    params = TaskIdParams(id='tid')

    event = MagicMock(spec=AgentStateChangedObservation)
    event.source = 'agent'
    event.message = 'Task stopped'
    event.agent_state = 'stopped'

    async def mock_async_iter():
        yield event

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: mock_async_iter(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    task = await handler._create_a2a_response('tid', params)
    assert task.status.state == TaskState.canceled


@pytest.mark.asyncio
async def test__create_a2a_response_input_required(monkeypatch):
    handler = A2aRequestHandler()
    params = TaskQueryParams(id='tid')

    event = MagicMock(spec=AgentStateChangedObservation)
    event.source = 'agent'
    event.message = 'awaiting_user_input'
    event.agent_state = 'awaiting_user_input'

    async def mock_async_iter():
        yield event

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: mock_async_iter(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    task = await handler._create_a2a_response('tid', params)
    assert task.status.state == TaskState.input_required


@pytest.mark.asyncio
async def test__create_a2a_response_input_data(monkeypatch):
    handler = A2aRequestHandler()
    params = TaskQueryParams(id='tid')

    event = MagicMock(spec=MessageAction)
    event.source = EventSource.AGENT
    event.message = 'test'
    event.agent_state = AgentState.AWAITING_USER_INPUT

    async def mock_async_iter():
        yield event

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: mock_async_iter(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    task = await handler._create_a2a_response('tid', params)
    assert task.status.state == TaskState.input_required


@pytest.mark.asyncio
async def test__create_a2a_response_classval_pass(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'tid'
    params = TaskIdParams(id=task_id)

    # AgentStateChangedObservation に似せたモックイベント
    event = MagicMock(spec=AgentStateChangedObservation)
    event.source = EventSource.AGENT
    event.message = 'Task is running'
    event.agent_state = 'working'
    event.id = 123

    message_id_existing = 'existing-message-id'
    handler._message_to_task_event[(task_id, event.id)] = message_id_existing

    class MockAsyncEventStore:
        def __aiter__(self):
            async def generator():
                yield event

            return generator()

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: MockAsyncEventStore(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    try:
        await handler._create_a2a_response(task_id, params)
    except ServerError:
        pass

    assert handler._message_to_task_event[(task_id, event.id)] == message_id_existing


@pytest.mark.asyncio
async def test__create_a2a_response_raises_not_cancelable(monkeypatch):
    handler = A2aRequestHandler()
    params = TaskIdParams(id='tid')

    event = MagicMock(spec=AgentStateChangedObservation)
    event.source = EventSource.AGENT
    event.message = 'Task is running'
    event.agent_state = 'working'

    async def mock_async_iter():
        yield event

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: mock_async_iter(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    with pytest.raises(ServerError) as e:
        await handler._create_a2a_response('tid', params)
    assert isinstance(e.value.error, TaskNotCancelableError)


@pytest.mark.asyncio
async def test__create_a2a_response_file_not_found(monkeypatch):
    handler = A2aRequestHandler()
    task_id = 'missing-task-id'
    params = TaskQueryParams(id=task_id)

    class FailingAsyncIterator:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise FileNotFoundError('Simulated missing file')

    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.EventStore',
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.AsyncEventStoreWrapper',
        lambda *args, **kwargs: FailingAsyncIterator(),
    )
    monkeypatch.setattr(
        'openhands.server.a2a.a2a_request_handler.conversation_manager',
        types.SimpleNamespace(file_store=None),
    )

    with pytest.raises(FileNotFoundError):
        await handler._create_a2a_response(task_id, params)


class ReqParams:
    def __init__(self):
        self.taskid = 'taskid123'
        self.message = Message(
            role='user',
            parts=[TextPart(kind='text', text='pythonでフィボナッチ数列を書いて')],
            metadata={'agent': 'CodeActAgent'},
            messageId='msg-001',
            contextId='ctx-456',
            kind='message',
        )

    def send_id(self):
        self.message.taskId = self.taskid
        params = MessageSendParams(
            message=self.message,
            taskId=self.taskid,
        )
        return params

    def send_notid(self):
        params = MessageSendParams(
            message=self.message,
        )
        return params

    def unsupported(self):
        message: dict[str, Any] = {
            'messageId': 'test',
            'role': 'user',
            'parts': [{'kind': 'text', 'text': 'pythonで四則演算のコードを作って'}],
        }
        params = SendMessageRequest(
            id='test', params=MessageSendParams(message=message)
        )
        return params


class Part(BaseModel):
    kind: Literal['text']
    text: str
