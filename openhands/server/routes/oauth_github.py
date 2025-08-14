from __future__ import annotations

import os
import urllib.parse
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, SecretStr

from openhands.integrations.service_types import ProviderType
from openhands.integrations.provider import ProviderToken
from openhands.server.config.server_config import ServerConfig
from openhands.server.dependencies import get_dependencies
from openhands.server.shared import server_config, config as app_config
from openhands.server.user_auth import get_user_id
from openhands.storage.data_models.user_secrets import UserSecrets
from openhands.storage.secrets.secrets_store import SecretsStore
from openhands.server.user_auth.github_cookie_auth import (
    GithubCookieUserAuth,
    SESSION_COOKIE_NAME,
)
from openhands.storage import get_file_store
from openhands.storage.secrets.file_secrets_store import FileSecretsStore


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
) -> Response:
    client_id = server_config.github_client_id
    client_secret = os.environ.get('GITHUB_APP_CLIENT_SECRET', '')
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail='GitHub OAuth not configured')

    base = str(request.base_url).rstrip('/')
    redirect_uri = f"{base}/api/auth/github/callback"

    # Exchange code for access token and fetch user info
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

        # fetch user
        user_headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {access_token}',
        }
        user_resp = await client.get('https://api.github.com/user', headers=user_headers)
        user = user_resp.json() if user_resp.status_code == 200 else {}

        # fetch primary email (optional)
        email_resp = await client.get('https://api.github.com/user/emails', headers=user_headers)
        email = None
        if email_resp.status_code == 200:
            try:
                primary = next((e for e in email_resp.json() if e.get('primary')), None)
                email = (primary or {}).get('email')
            except Exception:
                email = None

    # Determine GitHub user id and build a per-user secrets store
    gh_id = str(user.get('id') or '') or (user_id or 'github-user')
    file_store = get_file_store(
        app_config.file_store,
        app_config.file_store_path,
        app_config.file_store_web_hook_url,
        app_config.file_store_web_hook_headers,
    )
    secrets_store: SecretsStore = FileSecretsStore(
        file_store=file_store,
        path=f'users/{gh_id}/secrets.json',
    )

    # Persist token in SecretsStore under ProviderType.GITHUB
    existing = await secrets_store.load() or UserSecrets()
    provider_tokens = dict(existing.provider_tokens)
    provider_tokens[ProviderType.GITHUB] = ProviderToken.from_value(
        {'token': access_token, 'host': 'github.com'}
    )
    updated = existing.model_copy(update={'provider_tokens': provider_tokens})
    await secrets_store.store(updated)

    # Issue session cookie (JWT) to keep user signed in
    gh_login = user.get('login')
    gh_name = user.get('name')
    gh_avatar = user.get('avatar_url')
    token, max_age = GithubCookieUserAuth.issue_session_cookie(
        sub=gh_id,
        email=email,
        login=gh_login,
        name=gh_name,
        avatar_url=gh_avatar,
    )

    # Redirect to UI page (workspace or connect)
    frontend_redirect = os.environ.get('FRONTEND_REDIRECT_URL') or base
    response = RedirectResponse(url=frontend_redirect)

    # Secure, HTTP-only cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite='lax',
        path='/',
    )

    return response


@app.post('/logout')
async def github_logout() -> JSONResponse:
    # Clear the session cookie
    resp = JSONResponse({'message': 'logged out'})
    resp.delete_cookie(SESSION_COOKIE_NAME, path='/')
    return resp