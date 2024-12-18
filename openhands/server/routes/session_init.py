from typing import Annotated

from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import config
from openhands.storage.session_init_store import SessionInitStore
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api')

SessionInitStoreImpl = get_impl(SessionInitStore, config.session_init_store_class)  # type: ignore


@app.get('/session-init-data')
async def load_session_init_data(
    github_auth: Annotated[str | None, Header()] = None,
) -> SessionInitData | None:
    try:
        session_init_store = SessionInitStoreImpl.get_instance(config, github_auth)
        session_init_data = session_init_store.load()
        if not session_init_data:
            return None
        # Clear any sensitive data here
        session_init_data.llm_api_key = None
        session_init_data.github_token = None
        return session_init_data
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


@app.post('/session-init-data')
async def store_session_init_data(
    session_init_data: SessionInitData,
    github_auth: Annotated[str | None, Header()] = None,
) -> bool:
    try:
        session_init_store = SessionInitStoreImpl.get_instance(config, github_auth)
        session_init_data = session_init_store.store(session_init_data)
        return True
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )
