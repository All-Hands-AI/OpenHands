import os

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

_SESSION_API_KEY = os.getenv('SESSION_API_KEY')
_SESSION_API_KEY_HEADER = APIKeyHeader(name='X-Session-API-Key', auto_error=False)


def check_session_api_key(
    session_api_key: str | None = Depends(_SESSION_API_KEY_HEADER),
):
    if session_api_key != _SESSION_API_KEY:
        raise HTTPException(status)


def get_dependencies() -> list[Depends]:
    result = []
    if _SESSION_API_KEY:
        result.append(Depends(check_session_api_key))
    return result
