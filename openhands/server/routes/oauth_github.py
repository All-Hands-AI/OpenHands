from __future__ import annotations

import os
import urllib.parse
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, SecretStr

from openhands.integrations.service_types import ProviderType
from openhands.integrations.provider import ProviderToken
from openhands.server.config.server_config import ServerConfig
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import server_config, config as app_config
from openhands.server.user_auth import get_user_id, get_secrets_store
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore


app = APIRouter(prefix='/api/auth/github', dependencies=get_dependencies())


class OAuthStartResponse(BaseModel):
    auth_url: str


@app.get('/start', response_model=OAuthStartResponse)
async def github_oauth_start(request: Request) -> OAuthStartResponse:
    client_id = server_config.github_client_id
    if not client_id:
        raise HTTPException(status_code=400, detail='GITHUB_APP_CLIENT_ID not set')

    # redirect back to this server
    base = str(request.base_url).rstrip('/')
    redirect_uri = f"{base}/api/auth/github/callback"

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'repo read:user user:email',
        'allow_signup': 'false',
    }
    url = 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)
    return OAuthStartResponse(auth_url=url)


@app.get('/callback', response_model=None)
async def github_oauth_callback(
    request: Request,
    code: str,
    state: str | None = None,
    user_id: str | None = Depends(get_user_id),
    secrets_store: SecretsStore = Depends(get_secrets_store),
) -> RedirectResponse:
    client_id = server_config.github_client_id
    client_secret = os.environ.get('GITHUB_APP_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail='GitHub OAuth not configured')

    base = str(request.base_url).rstrip('/')
    redirect_uri = f"{base}/api/auth/github/callback"

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        headers = {'Accept': 'application/json'}
        token_resp = await client.post(
            'https://github.com/login/oauth/access_token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
            },
            headers=headers,
        )
        token_json = token_resp.json()
    access_token = token_json.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Failed to obtain access token')

    # Persist token in SecretsStore under ProviderType.GITHUB
    existing = await secrets_store.load() or UserSecrets()
    provider_tokens = dict(existing.provider_tokens)
    provider_tokens[ProviderType.GITHUB] = ProviderToken.from_value(
        {'token': access_token, 'host': 'github.com'}
    )
    updated = existing.model_copy(update={'provider_tokens': provider_tokens})
    await secrets_store.store(updated)

    # Redirect to UI page (workspace or connect)
    frontend_redirect = os.environ.get('FRONTEND_REDIRECT_URL')
    if not frontend_redirect:
        frontend_redirect = base  # default to root
    return RedirectResponse(url=frontend_redirect)