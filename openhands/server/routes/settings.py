from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_user_id
from openhands.server.services.github_service import GitHubService
from openhands.server.settings import Settings
from openhands.server.shared import config, openhands_config
from openhands.storage.conversation.conversation_store import ConversationStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.async_utils import call_sync_from_async
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api')

SettingsStoreImpl = get_impl(SettingsStore, openhands_config.settings_store_class)  # type: ignore
ConversationStoreImpl = get_impl(
    ConversationStore,  # type: ignore
    openhands_config.conversation_store_class,
)


@app.get('/settings')
async def load_settings(request: Request) -> Settings | None:
    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
        settings = await settings_store.load()
        if not settings:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Settings not found'},
            )

        # For security reasons we don't ever send the api key to the client
        github_token = settings.github_token or request.state.github_token
        settings.llm_api_key = 'SET' if settings.llm_api_key else None
        settings.github_token_is_set = True if github_token else False
        settings.github_token = None

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
    # Check if token is valid
    if settings.github_token:
        try:
            # We check if the token is valid by getting the user
            # If the token is invalid, this will raise an exception
            github = GitHubService(settings.github_token)
            await call_sync_from_async(github.get_user)
        except Exception as e:
            logger.warning(f'Invalid GitHub token: {e}')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Invalid GitHub token'},
            )

    try:
        settings_store = await SettingsStoreImpl.get_instance(
            config, get_user_id(request)
        )
        existing_settings = await settings_store.load()
        logger.info(f'Storing settings: {settings}')
        logger.info(f'Existing settings: {existing_settings}')

        if existing_settings:
            # LLM key isn't on the frontend, so we need to keep it if unset
            if settings.llm_api_key is None:
                settings.llm_api_key = existing_settings.llm_api_key

            if settings.github_token is None:
                settings.github_token = existing_settings.github_token

        response = JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Settings stored'},
        )

        if settings.unset_github_token:
            settings.github_token = None
            settings.unset_github_token = None

        # Update sandbox config with new settings
        if settings.remote_runtime_resource_factor is not None:
            config.sandbox.remote_runtime_resource_factor = (
                settings.remote_runtime_resource_factor
            )

        await settings_store.store(settings)
        return response
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )
