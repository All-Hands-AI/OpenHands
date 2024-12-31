import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from github import Github
from pydantic import BaseModel

from openhands.core.logger import openhands_logger as logger
from openhands.server.data_models.conversation_metadata import ConversationMetadata
from openhands.server.routes.settings import ConversationStoreImpl, SettingsStoreImpl
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import config, session_manager
from openhands.utils.async_utils import call_sync_from_async

app = APIRouter(prefix='/api')


class InitSessionRequest(BaseModel):
    github_token: str | None = None
    latest_event_id: int = -1
    selected_repository: str | None = None
    args: dict | None = None


@app.post('/conversations')
async def new_conversation(request: Request, data: InitSessionRequest):
    """Initialize a new session or join an existing one.
    After successful initialization, the client should connect to the WebSocket
    using the returned conversation ID
    """
    logger.info('Initializing new conversation')
    github_token = ''
    if data.github_token:
        github_token = data.github_token

    logger.info('Loading settings')
    settings_store = await SettingsStoreImpl.get_instance(config, github_token)
    settings = await settings_store.load()
    logger.info('Settings loaded')

    session_init_args: dict = {}
    if settings:
        session_init_args = {**settings.__dict__, **session_init_args}

    session_init_args['github_token'] = github_token
    session_init_args['selected_repository'] = data.selected_repository
    conversation_init_data = ConversationInitData(**session_init_args)

    logger.info('Loading conversation store')
    conversation_store = await ConversationStoreImpl.get_instance(config, github_token)
    logger.info('Conversation store loaded')

    conversation_id = uuid.uuid4().hex
    while await conversation_store.exists(conversation_id):
        logger.warning(f'Collision on conversation ID: {conversation_id}. Retrying...')
        conversation_id = uuid.uuid4().hex
    logger.info(f'New conversation ID: {conversation_id}')

    user_id = ''
    if data.github_token:
        logger.info('Fetching Github user ID')
        with Github(data.github_token) as g:
            gh_user = await call_sync_from_async(g.get_user)
            user_id = gh_user.id

    logger.info(f'Saving metadata for conversation {conversation_id}')
    await conversation_store.save_metadata(
        ConversationMetadata(
            conversation_id=conversation_id,
            github_user_id=user_id,
            selected_repository=data.selected_repository,
        )
    )

    logger.info(f'Starting agent loop for conversation {conversation_id}')
    await session_manager.maybe_start_agent_loop(
        conversation_id, conversation_init_data
    )
    logger.info(f'Finished initializing conversation {conversation_id}')
    return JSONResponse(content={'status': 'ok', 'conversation_id': conversation_id})
