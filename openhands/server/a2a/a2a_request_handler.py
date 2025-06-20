import asyncio
import time
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from a2a.server.events import Event
from a2a.types import (
    Message,
    MessageSendParams,
    Role,
    Task,
    TaskIdParams,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskState,
    TaskStatus,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from a2a.utils.telemetry import SpanKind, trace_class

from openhands.core.schema import ActionType
from openhands.core.schema.agent import AgentState
from openhands.events.action import NullAction, SystemMessageAction
from openhands.events.action.agent import RecallAction
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.event import Event, EventSource
from openhands.events.event_store import EventStore
from openhands.events.observation import NullObservation
from openhands.events.observation.agent import (
    AgentStateChangedObservation,
    RecallObservation,
)
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.session.session import Session
from openhands.server.shared import (
    SecretsStoreImpl,
    SettingsStoreImpl,
    config,
    conversation_manager,
    file_store,
    server_config,
)
from openhands.server.types import AppMode
from openhands.storage.data_models.user_secrets import UserSecrets


@trace_class(kind=SpanKind.SERVER)
class A2aRequestHandler:

    _task_id_to_sessions: dict[str, Session] = {}
    _message_to_task_event: dict[tuple[str, int], str] = {}

    async def on_cancel_task(self, params: TaskIdParams, context) -> Task | None:
        task_id = self._params_get_task_id(params)

        if task_id in A2aRequestHandler._task_id_to_sessions:
            session = A2aRequestHandler._task_id_to_sessions[task_id]

            data = self._convert_a2a_params_to_dict(params)
            await asyncio.create_task(session.dispatch(data))
            time.sleep(1)

            return await self._create_a2a_response(task_id, params)
        else:
            raise ServerError(error=TaskNotFoundError())

    async def on_message_send(
        self, params: MessageSendParams, context
    ) -> Message | Task:
        task_id = self._params_get_task_id(params)
        conversation_init_data = await self._conversation_init_data_set(params)
        if task_id in A2aRequestHandler._task_id_to_sessions:
            session = A2aRequestHandler._task_id_to_sessions[task_id]
        else:
            session = Session(
                sid=task_id,
                file_store=file_store,
                config=config,
                sio=None,
            )

        asyncio.create_task(
            self._background_task(session, conversation_init_data, params, task_id)
        )

        response = self._server_preparation(task_id, params)
        return response

    async def on_message_send_stream(
        self, params: MessageSendParams
    ) -> AsyncGenerator[Event]:
        raise ServerError(error=UnsupportedOperationError())

    async def on_set_task_push_notification_config(
        self, params: TaskPushNotificationConfig
    ) -> TaskPushNotificationConfig:
        raise ServerError(error=UnsupportedOperationError())

    async def on_get_task_push_notification_config(
        self, params: TaskIdParams
    ) -> TaskPushNotificationConfig:
        raise ServerError(error=UnsupportedOperationError())

    async def on_resubscribe_to_task(
        self, params: TaskIdParams
    ) -> AsyncGenerator[Event]:
        raise ServerError(error=UnsupportedOperationError())

    def should_add_push_info(self, params: MessageSendParams) -> bool:
        raise ServerError(error=UnsupportedOperationError())

    async def on_get_task(self, params: TaskQueryParams, context) -> Task | None:
        task_id = self._params_get_task_id(params)
        if task_id in A2aRequestHandler._task_id_to_sessions:
            return await self._create_a2a_response(task_id, params)
        else:
            raise ServerError(error=TaskNotFoundError())

    def _convert_a2a_params_to_dict(self, params) -> Dict[str, Any]:

        match params:
            case MessageSendParams():
                # with stream
                msg = params.message
                event_dict = {
                    "action": ActionType.MESSAGE,
                    "args": {
                        "content": msg.parts[0].root.text,
                        "image_urls": [],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "messageId": msg.messageId,
                    "source": EventSource.USER,
                }
            case _ if isinstance(params, (TaskQueryParams, TaskIdParams)):
                # with tasks/pushNotificationConfig/get tasks/resubscribe
                event_dict = {
                    "action": ActionType.CHANGE_AGENT_STATE,
                    "args": {
                        "agent_state": AgentState.STOPPED,
                    },
                    "source": EventSource.USER,
                }
            case _:
                raise ServerError(error=UnsupportedOperationError())

        return event_dict

    async def _create_a2a_response(
        self, task_id, params: MessageSendParams | TaskQueryParams | TaskIdParams
    ):
        try:

            event_store = EventStore(
                task_id, conversation_manager.file_store, user_id=None
            )

            async_store = AsyncEventStoreWrapper(event_store, 0)

            responses = []
            async for event in async_store:
                agent_state = getattr(event, 'agent_state', "")
                if (task_id, event.id) in self._message_to_task_event:
                    message_id = self._message_to_task_event[(task_id, event.id)]
                elif (
                    event.source == EventSource.USER
                    or event.source == EventSource.AGENT
                ):
                    message_id = uuid4().hex
                    self._message_to_task_event[(task_id, event.id)] = message_id

                match agent_state:
                    case AgentState.FINISHED:
                        taskStatus = TaskState.completed
                    case AgentState.STOPPED:
                        taskStatus = TaskState.canceled
                    case AgentState.AWAITING_USER_INPUT:
                        taskStatus = TaskState.input_required
                    case _:
                        taskStatus = TaskState.working

                if isinstance(
                    event,
                    (
                        NullAction,
                        NullObservation,
                        RecallAction,
                        RecallObservation,
                        SystemMessageAction,
                        AgentStateChangedObservation,
                    ),
                ):
                    continue
                else:
                    response_dict = {
                        'source': event.source,
                        'message': event.message,
                        'agent_state': getattr(event, 'agent_state', ""),
                        'message_id': message_id,
                    }
                    responses.append(response_dict)

            if isinstance(params, TaskIdParams) and agent_state != AgentState.STOPPED:
                raise ServerError(error=TaskNotCancelableError())

            messages = []
            for response in responses:
                message = Message(
                    role=Role.agent,
                    parts=[{"kind": "text", "text": response['message']}],
                    messageId=response['message_id'],
                    taskId=task_id,
                    kind="message",
                )
                messages.append(message)

            task = Task(
                id=task_id,
                contextId=uuid4().hex,
                status=TaskStatus(state=taskStatus),
                history=messages,
                kind="task",
            )

            return task
        except FileNotFoundError as exc:
            raise FileNotFoundError from exc

    def _params_get_task_id(
        self, params: MessageSendParams | TaskQueryParams | TaskIdParams
    ):
        match params:
            case MessageSendParams():
                # with stream
                if params.message.taskId is None:
                    task_id = uuid4().hex
                else:
                    task_id = params.message.taskId

            case _ if isinstance(params, (TaskQueryParams, TaskIdParams)):
                # with tasks/pushNotificationConfig/get tasks/resubscribe
                task_id = params.id

            case _:
                raise ServerError(error=UnsupportedOperationError())

        return task_id

    async def _conversation_init_data_set(
        self,
        params: MessageSendParams | TaskQueryParams | TaskIdParams,
    ):
        task_id = self._params_get_task_id(params)

        settings_store = await SettingsStoreImpl.get_instance(config, user_id=task_id)
        settings = await settings_store.load()

        secrets_store = await SecretsStoreImpl.get_instance(config, user_id=task_id)
        user_secrets: UserSecrets | None = await secrets_store.load()

        if not settings:
            raise ConnectionRefusedError(
                'Settings not found', {'msg_id': 'CONFIGURATION$SETTINGS_NOT_FOUND'}
            )

        session_init_args: dict = {}
        if not (params.metadata is None):
            session_init_args['agent'] = params.metadata['agent']

        if settings:
            session_init_args = {**settings.__dict__, **session_init_args}

        if server_config.app_mode != AppMode.SAAS and user_secrets:
            git_provider_tokens = user_secrets.provider_tokens
            session_init_args['git_provider_tokens'] = git_provider_tokens

        if user_secrets:
            session_init_args['custom_secrets'] = user_secrets.custom_secrets

        conversation_init_data = ConversationInitData(**session_init_args)

        return conversation_init_data

    def _server_preparation(self, task_id, params):

        message = Message(
            role=Role.agent,
            parts=[{"kind": "text", "text": "server is preparation"}],
            messageId=params.message.messageId,
            taskId=task_id,
            kind="message",
        )

        task = Task(
            id=task_id,
            contextId=uuid4().hex,
            status=TaskStatus(state=TaskState.working),
            history=[message],
            kind="task",
        )

        return task

    async def _background_task(self, session, conversation_init_data, params, task_id):
        if task_id not in self._task_id_to_sessions:
            await session.initialize_agent(
                conversation_init_data, None, replay_json=None
            )
        data = self._convert_a2a_params_to_dict(params)
        await session.dispatch(data)

        self._task_id_to_sessions[task_id] = session

        event_store = EventStore(task_id, conversation_manager.file_store, user_id=None)

        async_store = AsyncEventStoreWrapper(event_store, 0)

        message_id = (
            params.message.messageId if params.message.messageId != "" else uuid4().hex
        )
        async for event in async_store:
            if (task_id, event.id) not in self._message_to_task_event:
                if event.source == EventSource.USER:
                    self._message_to_task_event[(task_id, event.id)] = message_id
                elif event.source == EventSource.AGENT:
                    self._message_to_task_event[(task_id, event.id)] = uuid4().hex
