from typing import Annotated

from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.settings import Settings
from openhands.server.shared import config, openhands_config
from openhands.storage.settings_store import SettingsStore
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api')

SettingsStoreImpl = get_impl(SettingsStore, openhands_config.settings_store_class)  # type: ignore


@app.get('/settings')
async def load_settings(
    github_auth: Annotated[str | None, Header()] = None,
) -> Settings | None:
    try:
        settings_store = await SettingsStoreImpl.get_instance(config, github_auth)
        settings = await settings_store.load()
        if settings:
            # For security reasons we don't ever send the api key to the client
            settings.llm_api_key = None
        return settings
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/settings')
async def store_settings(
    settings: Settings,
    github_auth: Annotated[str | None, Header()] = None,
) -> bool:
    try:
        settings_store = await SettingsStoreImpl.get_instance(config, github_auth)
        existing_settings = await settings_store.load()
        if existing_settings:
            if settings.llm_api_key is None:
                settings.llm_api_key = existing_settings.llm_api_key
        return await settings_store.store(settings)
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )
