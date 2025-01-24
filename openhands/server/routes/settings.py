from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_user_id
from openhands.server.services.github_service import GitHubService
from openhands.server.settings import Settings, SettingsWithTokenMeta
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
async def load_settings(request: Request) -> SettingsWithTokenMeta | None:
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

        github_token = request.state.github_token
        settings_with_token_data = SettingsWithTokenMeta(
            **settings.model_dump(),
            github_token_is_set=bool(github_token),
        )

        del settings_with_token_data.github_token
        return settings_with_token_data
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/settings')
async def store_settings(
    request: Request,
    settings: SettingsWithTokenMeta,
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

        # Update sandbox config with new settings
        if settings.remote_runtime_resource_factor is not None:
            config.sandbox.remote_runtime_resource_factor = (
                settings.remote_runtime_resource_factor
            )

        settings = convert_to_settings(settings)

        await settings_store.store(settings)
        return response
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


def convert_to_settings(settings_with_token_data: SettingsWithTokenMeta) -> Settings:
    settings_data = settings_with_token_data.model_dump()

    # Filter out additional fields from `SettingsWithTokenData`
    filtered_settings_data = {
        key: value
        for key, value in settings_data.items()
        if key in Settings.model_fields  # Ensures only `Settings` fields are included
    }

    return Settings(**filtered_settings_data)
