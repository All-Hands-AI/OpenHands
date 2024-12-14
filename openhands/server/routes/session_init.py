from typing import Annotated

import jwt
from fastapi import APIRouter, Header, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.server.github_utils import UserVerifier, get_github_user_obj
from openhands.server.session.session_init_data import SessionInitData
from openhands.server.shared import config
from openhands.storage.item_store import ItemStore
from openhands.utils.import_utils import get_impl

app = APIRouter(prefix='/api')

session_init_data_store = get_impl(ItemStore, config.item_store_class)()  # type: ignore


@app.get('/session-init-data')
async def load_session_init_data(
    github_auth: Annotated[str | None, Header()] = None,
) -> SessionInitData | None:
    try:
        id = await get_user_id(github_auth)
        session_init_data = session_init_data_store.load(id)
        if not session_init_data:
            return None
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
        id = await get_user_id(github_auth)
        session_init_data = session_init_data_store.store(id, session_init_data)
        return True
    except Exception as e:
        logger.warning(f'Invalid token: {e}')
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Invalid token'},
        )


async def get_user_id(github_auth: str | None) -> str:
    user_verifier = UserVerifier()
    if not user_verifier.is_active() and not github_auth:
        return 'session_init_data'
    values = jwt.decode(github_auth, config.jwt_secret, algorithms=['HS256'])
    github_token = values['github_token']
    user = await get_github_user_obj(github_token)
    id = user.id
    return id
