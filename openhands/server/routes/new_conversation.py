import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from github import Github
from pydantic import BaseModel

from openhands.server.routes.settings import SettingsStoreImpl
from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import config, session_manager
from openhands.storage.conversation.conversation_store import (
    ConversationMetadata,
    ConversationStore,
)
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api')


class InitSessionRequest(BaseModel):
    token: str | None = None
    github_token: str | None = None
    latest_event_id: int = -1
    args: dict | None = None
    selected_repository: str | None = None


@app.post('/conversation')
async def new_conversation(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.
    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID
    """
    github_token = ''
    if data.github_token:
        github_token = data.github_token

    session_init_args: dict = {}
    settings_store = await SettingsStoreImpl.get_instance(config, github_token)
    settings = await settings_store.load()
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}

    session_init_args['github_token'] = github_token
    session_init_args['selected_repository'] = data.selected_repository
    session_init_data = SessionInitData(**session_init_args)

    conversation_store = await ConversationStore.get_instance(config)

    conversation_id = uuid.uuid4().hex
    while conversation_store.exists(conversation_id):
        conversation_id = uuid.uuid4().hex

    user_id = ''
    if data.github_token:
        g = Github(data.github_token)
        gh_user = await call_sync_from_async(g.get_user)
        user_id = gh_user.id

    await conversation_store.save_metadata(
        ConversationMetadata(
            conversation_id=conversation_id,
            github_user_id=user_id,
            selected_repository=data.selected_repository,
        )
    )

    await session_manager.start_agent_loop(conversation_id, session_init_data)
    return JSONResponse(content={'status': 'ok', 'conversation_id': conversation_id})
