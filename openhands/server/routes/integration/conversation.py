import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.core.schema.action import ActionType
from openhands.events.action.agent import RecallAction
from openhands.events.action.empty import NullAction
from openhands.events.async_event_store_wrapper import AsyncEventStoreWrapper
from openhands.events.event_store import EventStore
from openhands.events.observation.agent import AgentStateChangedObservation
from openhands.events.observation.empty import NullObservation
from openhands.events.serialization.event import event_to_dict
from openhands.server.auth import (
    get_github_user_id,
    get_user_id,
)
from openhands.server.data_models.conversation_info import ConversationDetailInfo
from openhands.server.modules.conversation import conversation_module
from openhands.server.modules.space import SpaceModule
from openhands.server.routes.manage_conversations import (
    InitSessionRequest,
    get_default_conversation_title,
    new_conversation,
)
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
    conversation_manager,
)
from openhands.storage.data_models.conversation_status import ConversationStatus

conversation_router = APIRouter(prefix='/conversations')


class CreatNewConversationIntegrationRequest(BaseModel):
    initial_user_msg: str | None = None
    research_mode: str | None = None
    space_id: int | None = None
    space_section_id: int | None = None
    thread_follow_up: int | None = None
    followup_discover_id: str | None = None
    mcp_disable: dict[str, bool] | None = None
    system_prompt: str | None = None
    image_urls: list[str] | None = None


@conversation_router.post('')
async def integration_new_conversation(
    request: Request, data: CreatNewConversationIntegrationRequest
):
    new_conversation_data = InitSessionRequest(**data.model_dump())
    new_conversation_result = await new_conversation(request, new_conversation_data)

    try:
        new_conversation_json = json.loads(new_conversation_result.body)
        conversation_id = new_conversation_json.get('conversation_id')
    except Exception:
        conversation_id = None

    if conversation_id and data.space_id and data.space_section_id:
        space_module = SpaceModule(request.headers.get('Authorization'))
        await space_module.update_space_section_history(
            space_id=str(data.space_id),
            section_id=str(data.space_section_id),
            conversation_id=conversation_id,
        )
    return new_conversation_result


@conversation_router.get('/{conversation_id}')
async def integration_get_conversation(
    conversation_id: str, request: Request
) -> ConversationDetailInfo | None:
    user_id = get_user_id(request)
    conversation = await conversation_module._get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail='Conversation not found')

    default_title = get_default_conversation_title(conversation_id)
    conversation_info = ConversationDetailInfo(
        conversation_id=conversation_id,
        title=default_title,
    )
    conversation_store = await ConversationStoreImpl.get_instance(
        config, user_id, get_github_user_id(request)
    )
    try:
        metadata = await conversation_store.get_metadata(conversation_id)
        is_running = await conversation_manager.is_agent_loop_running(conversation_id)
        title = metadata.title
        if not title:
            title = default_title
        conversation_info = ConversationDetailInfo(
            conversation_id=metadata.conversation_id,
            title=title,
            last_updated_at=metadata.last_updated_at,
            created_at=metadata.created_at,
            selected_repository=metadata.selected_repository,
            status=(
                ConversationStatus.RUNNING
                if is_running
                else ConversationStatus.FINISHED
            ),
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail='Conversation not found')

    # eventstore
    event_store = EventStore(
        conversation_id,
        conversation_manager.file_store,
        conversation.user_id,
    )
    if not event_store:
        return conversation_info
    async_store = AsyncEventStoreWrapper(event_store, 0)
    result = []
    streaming_events = []
    async for event in async_store:
        try:
            if not event:
                continue
            if isinstance(
                event,
                (
                    NullAction,
                    NullObservation,
                    RecallAction,
                    AgentStateChangedObservation,
                ),
            ):
                continue
            event_dict = event_to_dict(event)
            if not event_dict:
                continue
            if event_dict.get('source') not in ['user', 'agent']:
                continue
            if event_dict.get('action') == ActionType.STREAMING_MESSAGE:
                streaming_events.append(event_dict)
                continue
            if streaming_events:
                result.append(_handle_streaming_message(streaming_events))
                streaming_events = []
            result.append(event_dict)
        except Exception as e:
            logger.error(f'Error converting event to dict: {str(e)}')
    if streaming_events:
        result.append(_handle_streaming_message(streaming_events))
    conversation_info.events = result
    if getattr(conversation, 'final_result', None):
        conversation_info.final_result = conversation.final_result
    return conversation_info


def _handle_streaming_message(streaming_events: list[dict] | None) -> dict | None:
    if not streaming_events:
        return None
    last_event = streaming_events[-1]
    last_event['message'] = ''.join([e['message'] for e in streaming_events]).strip()
    streaming_events = []
    return last_event
