import warnings
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional
from urllib.parse import quote

import posthog
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import SecretStr
from server.auth.auth_utils import user_verifier
from server.auth.constants import (
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_REALM_NAME,
    KEYCLOAK_SERVER_URL_EXT,
)
from server.auth.gitlab_sync import schedule_gitlab_repo_sync
from server.auth.saas_user_auth import SaasUserAuth
from server.auth.token_manager import TokenManager
from server.config import sign_token
from server.constants import IS_FEATURE_ENV
from server.routes.event_webhook import _get_session_api_key, _get_user_id
from storage.database import session_maker
from storage.user_settings import UserSettings

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.provider import ProviderHandler
from openhands.integrations.service_types import ProviderType, TokenResponse
from openhands.server.services.conversation_service import create_provider_tokens_object
from openhands.server.shared import config
from openhands.server.user_auth import get_access_token
from openhands.server.user_auth.user_auth import get_user_auth

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

api_router = APIRouter(prefix='/api')
oauth_router = APIRouter(prefix='/oauth')

token_manager = TokenManager()


def set_response_cookie(
    request: Request,
    response: Response,
    keycloak_access_token: str,
    keycloak_refresh_token: str,
    secure: bool = True,
    accepted_tos: bool = False,
):
    # Create a signed JWT token
    cookie_data = {
        'access_token': keycloak_access_token,
        'refresh_token': keycloak_refresh_token,
        'accepted_tos': accepted_tos,
    }
    signed_token = sign_token(cookie_data, config.jwt_secret.get_secret_value())  # type: ignore

    # Set secure cookie with signed token
    domain = get_cookie_domain(request)
    if domain:
        response.set_cookie(
            key='keycloak_auth',
            value=signed_token,
            domain=domain,
            httponly=True,
            secure=secure,
            samesite=get_cookie_samesite(request),
        )
    else:
        response.set_cookie(
            key='keycloak_auth',
            value=signed_token,
            httponly=True,
            secure=secure,
            samesite=get_cookie_samesite(request),
        )


def get_cookie_domain(request: Request) -> str | None:
    # for now just use the full hostname except for staging stacks.
    return (
        None
        if (request.url.hostname or '').endswith('staging.all-hand.dev')
        else request.url.hostname
    )


def get_cookie_samesite(request: Request) -> Literal['lax', 'strict']:
    # for localhost and feature/staging stacks we set it to 'lax' as the cookie domain won't allow 'strict'
    return (
        'lax'
        if request.url.hostname == 'localhost'
        or (request.url.hostname or '').endswith('staging.all-hands.dev')
        else 'strict'
    )


@oauth_router.get('/keycloak/callback')
async def keycloak_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    redirect_url: str = state if state else str(request.base_url)
    if not code:
        # check if this is a forward from the account linking page
        if (
            error == 'temporarily_unavailable'
            and error_description == 'authentication_expired'
        ):
            return RedirectResponse(redirect_url, status_code=302)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Missing code in request params'},
        )
    scheme = 'http' if request.url.hostname == 'localhost' else 'https'
    redirect_uri = f'{scheme}://{request.url.netloc}{request.url.path}'
    logger.debug(f'code: {code}, redirect_uri: {redirect_uri}')

    (
        keycloak_access_token,
        keycloak_refresh_token,
    ) = await token_manager.get_keycloak_tokens(code, redirect_uri)
    if not keycloak_access_token or not keycloak_refresh_token:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Problem retrieving Keycloak tokens'},
        )

    user_info = await token_manager.get_user_info(keycloak_access_token)
    logger.debug(f'user_info: {user_info}')
    if 'sub' not in user_info or 'preferred_username' not in user_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Missing user ID or username in response'},
        )

    user_id = user_info['sub']
    # default to github IDP for now.
    # TODO: remove default once Keycloak is updated universally with the new attribute.
    idp: str = user_info.get('identity_provider', ProviderType.GITHUB.value)
    logger.info(f'Full IDP is {idp}')
    idp_type = 'oidc'
    if ':' in idp:
        idp, idp_type = idp.rsplit(':', 1)
        idp_type = idp_type.lower()

    await token_manager.store_idp_tokens(
        ProviderType(idp), user_id, keycloak_access_token
    )

    username = user_info['preferred_username']
    if user_verifier.is_active() and not user_verifier.is_user_allowed(username):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'Not authorized via waitlist'},
        )

    valid_offline_token = (
        await token_manager.validate_offline_token(user_id=user_info['sub'])
        if idp_type != 'saml'
        else True
    )

    logger.debug(
        f'keycloakAccessToken: {keycloak_access_token}, keycloakUserId: {user_id}'
    )

    # adding in posthog tracking

    # If this is a feature environment, add "FEATURE_" prefix to user_id for PostHog
    posthog_user_id = f'FEATURE_{user_id}' if IS_FEATURE_ENV else user_id

    try:
        posthog.identify(
            posthog_user_id,
            {
                '$set': {
                    'user_id': posthog_user_id,  # Explicitly set as property
                    'original_user_id': user_id,  # Store the original user_id
                    'is_feature_env': IS_FEATURE_ENV,  # Track if this is a feature environment
                }
            },
        )
    except Exception as e:
        logger.error(
            'auth:posthog_identify:failed',
            extra={
                'user_id': user_id,
                'error': str(e),
            },
        )
        # Continue execution as this is not critical

    logger.info(
        'user_logged_in',
        extra={
            'idp': idp,
            'idp_type': idp_type,
            'posthog_user_id': posthog_user_id,
            'is_feature_env': IS_FEATURE_ENV,
        },
    )

    if not valid_offline_token:
        redirect_url = (
            f'{KEYCLOAK_SERVER_URL_EXT}/realms/{KEYCLOAK_REALM_NAME}/protocol/openid-connect/auth'
            f'?client_id={KEYCLOAK_CLIENT_ID}&response_type=code'
            f'&kc_idp_hint={idp}'
            f'&redirect_uri={scheme}%3A%2F%2F{request.url.netloc}%2Foauth%2Fkeycloak%2Foffline%2Fcallback'
            f'&scope=openid%20email%20profile%20offline_access'
            f'&state={state}'
        )

    has_accepted_tos = False
    with session_maker() as session:
        user_settings = (
            session.query(UserSettings)
            .filter(UserSettings.keycloak_user_id == user_id)
            .first()
        )
        has_accepted_tos = (
            user_settings is not None and user_settings.accepted_tos is not None
        )

    # If the user hasn't accepted the TOS, redirect to the TOS page
    if not has_accepted_tos:
        encoded_redirect_url = quote(redirect_url, safe='')
        tos_redirect_url = (
            f'{request.base_url}accept-tos?redirect_url={encoded_redirect_url}'
        )
        response = RedirectResponse(tos_redirect_url, status_code=302)
    else:
        response = RedirectResponse(redirect_url, status_code=302)

    set_response_cookie(
        request=request,
        response=response,
        keycloak_access_token=keycloak_access_token,
        keycloak_refresh_token=keycloak_refresh_token,
        secure=True if scheme == 'https' else False,
        accepted_tos=has_accepted_tos,
    )

    # Sync GitLab repos & set up webhooks
    # Use Keycloak access token (first-time users lack offline token at this stage)
    # Normally, offline token is used to fetch GitLab token via user_id
    schedule_gitlab_repo_sync(user_id, SecretStr(keycloak_access_token))
    return response


@oauth_router.get('/keycloak/offline/callback')
async def keycloak_offline_callback(code: str, state: str, request: Request):
    if not code:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Missing code in request params'},
        )
    scheme = 'https'
    if request.url.hostname == 'localhost':
        scheme = 'http'
    redirect_uri = f'{scheme}://{request.url.netloc}{request.url.path}'
    logger.debug(f'code: {code}, redirect_uri: {redirect_uri}')

    (
        keycloak_access_token,
        keycloak_refresh_token,
    ) = await token_manager.get_keycloak_tokens(code, redirect_uri)
    if not keycloak_access_token or not keycloak_refresh_token:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Problem retrieving Keycloak tokens'},
        )

    user_info = await token_manager.get_user_info(keycloak_access_token)
    logger.debug(f'user_info: {user_info}')
    if 'sub' not in user_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'error': 'Missing Keycloak ID in response'},
        )

    await token_manager.store_offline_token(
        user_id=user_info['sub'], offline_token=keycloak_refresh_token
    )

    return RedirectResponse(state if state else request.base_url, status_code=302)


@oauth_router.get('/github/callback')
async def github_dummy_callback(request: Request):
    """Callback for GitHub that just forwards the user to the app base URL."""
    return RedirectResponse(request.base_url, status_code=302)


@api_router.post('/authenticate')
async def authenticate(request: Request):
    try:
        await get_access_token(request)
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={'message': 'User authenticated'}
        )
    except Exception:
        # For any error during authentication, clear the auth cookie and return 401
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'User is not authenticated'},
        )

        # Delete the auth cookie if it exists
        keycloak_auth_cookie = request.cookies.get('keycloak_auth')
        if keycloak_auth_cookie:
            response.delete_cookie(
                key='keycloak_auth',
                domain=get_cookie_domain(request),
                samesite=get_cookie_samesite(request),
            )

        return response


@api_router.post('/accept_tos')
async def accept_tos(request: Request):
    user_auth: SaasUserAuth = await get_user_auth(request)
    access_token = await user_auth.get_access_token()
    refresh_token = user_auth.refresh_token
    user_id = await user_auth.get_user_id()

    if not access_token or not refresh_token or not user_id:
        logger.warning(
            f'accept_tos: One or more is None: access_token {access_token}, refresh_token {refresh_token}, user_id {user_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={'error': 'User is not authenticated'},
        )

    # Get redirect URL from request body
    body = await request.json()
    redirect_url = body.get('redirect_url', str(request.base_url))

    # Update user settings with TOS acceptance
    with session_maker() as session:
        user_settings = (
            session.query(UserSettings)
            .filter(UserSettings.keycloak_user_id == user_id)
            .first()
        )

        if user_settings:
            user_settings.accepted_tos = datetime.now(timezone.utc)
            session.merge(user_settings)
        else:
            # Create user settings if they don't exist
            user_settings = UserSettings(
                keycloak_user_id=user_id,
                accepted_tos=datetime.now(timezone.utc),
                user_version=0,  # This will trigger a migration to the latest version on next load
            )
            session.add(user_settings)

        session.commit()

    logger.info(f'User {user_id} accepted TOS')

    response = JSONResponse(
        status_code=status.HTTP_200_OK, content={'redirect_url': redirect_url}
    )

    set_response_cookie(
        request=request,
        response=response,
        keycloak_access_token=access_token.get_secret_value(),
        keycloak_refresh_token=refresh_token.get_secret_value(),
        secure=False if request.url.hostname == 'localhost' else True,
        accepted_tos=True,
    )
    return response


@api_router.post('/logout')
async def logout(request: Request):
    # Always create the response object first to ensure we can return it even if errors occur
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'message': 'User logged out'},
    )

    # Always delete the cookie regardless of what happens
    response.delete_cookie(
        key='keycloak_auth',
        domain=get_cookie_domain(request),
        samesite=get_cookie_samesite(request),
    )

    # Try to properly logout from Keycloak, but don't fail if it doesn't work
    try:
        user_auth: SaasUserAuth = await get_user_auth(request)
        if user_auth and user_auth.refresh_token:
            refresh_token = user_auth.refresh_token.get_secret_value()
            await token_manager.logout(refresh_token)
    except Exception as e:
        # Log any errors but don't fail the request
        logger.debug(f'Error during logout: {str(e)}')
        # We still want to clear the cookie and return success

    return response


@api_router.get('/refresh-tokens', response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    provider: ProviderType,
    sid: str,
    x_session_api_key: Annotated[str | None, Header(alias='X-Session-API-Key')],
) -> TokenResponse:
    """Return the latest token for a given provider."""
    user_id = _get_user_id(sid)
    session_api_key = await _get_session_api_key(user_id, sid)
    if session_api_key != x_session_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Forbidden')

    logger.info(f'Refreshing token for conversation {sid}')
    provider_handler = ProviderHandler(
        create_provider_tokens_object([provider]), external_auth_id=user_id
    )
    service = provider_handler._get_service(provider)
    token = await service.get_latest_token()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No token found for provider '{provider}'",
        )

    return TokenResponse(token=token.get_secret_value())
