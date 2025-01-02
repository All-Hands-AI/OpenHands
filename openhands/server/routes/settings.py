from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.settings import Settings
from openhands.server.shared import config, openhands_config
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api')

SettingsStoreImpl = get_impl(SettingsStore, openhands_config.settings_store_class)  # type: ignore
ConversationStoreImpl = get_impl(
    ConversationStore,  # type: ignore
    openhands_config.conversation_store_class,
)


@app.get('/settings')
async def load_settings(
    request: Request,
) -> Settings | None:
    github_token = ''
    if hasattr(request.state, 'github_token'):
        github_token = request.state.github_token
    try:
        settings_store = await SettingsStoreImpl.get_instance(config, github_token)
        settings = await settings_store.load()
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        # For security reasons we don't ever send the api key to the client
        settings.llm_api_key = 'SET' if settings.llm_api_key else None
        return settings
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/settings')
async def store_settings(
    request: Request,
    settings: Settings,
) -> JSONResponse:
    github_token = ''
    if hasattr(request.state, 'github_token'):
        github_token = request.state.github_token
    try:
        settings_store = await SettingsStoreImpl.get_instance(config, github_token)
        existing_settings = await settings_store.load()

        if existing_settings:
            # LLM key isn't on the frontend, so we need to keep it if unset
            if settings.llm_api_key is None:
                settings.llm_api_key = existing_settings.llm_api_key
        await settings_store.store(settings)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )
