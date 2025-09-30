from datetime import UTC, datetime
from typing import Callable

import jwt
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import SecretStr
from server.auth.auth_error import (
    AuthError,
    EmailNotVerifiedError,
    NoCredentialsError,
    TosNotAcceptedError,
)
from server.auth.gitlab_sync import schedule_gitlab_repo_sync
from server.auth.saas_user_auth import SaasUserAuth, token_manager
from server.constants import get_default_litellm_model
from server.routes.auth import (
    get_cookie_domain,
    get_cookie_samesite,
    set_response_cookie,
)
from storage.database import session_maker
from storage.subscription_access import SubscriptionAccess

from openhands.core.logger import openhands_logger as logger
from openhands.server.user_auth.user_auth import AuthType, get_user_auth
from openhands.server.utils import config
from openhands.storage.data_models.settings import Settings


class SetAuthCookieMiddleware:
    """Update the auth cookie with the current authentication state if it was refreshed before sending response to user.

    Deleting invalid cookies is handled by CookieError using FastAPIs standard error handling mechanism.
    """

    async def __call__(self, request: Request, call_next: Callable):
        keycloak_auth_cookie = request.cookies.get('keycloak_auth')
        logger.debug('request_with_cookie', extra={'cookie': keycloak_auth_cookie})
        try:
            if self._should_attach(request):
                self._check_tos(request)

            response: Response = await call_next(request)
            if not keycloak_auth_cookie:
                return response
            user_auth = self._get_user_auth(request)
            if not user_auth or user_auth.auth_type != AuthType.COOKIE:
                return response
            if user_auth.refreshed:
                set_response_cookie(
                    request=request,
                    response=response,
                    keycloak_access_token=user_auth.access_token.get_secret_value(),
                    keycloak_refresh_token=user_auth.refresh_token.get_secret_value(),
                    secure=False if request.url.hostname == 'localhost' else True,
                    accepted_tos=user_auth.accepted_tos,
                )

                # On re-authentication (token refresh), kick off background sync for GitLab repos
                schedule_gitlab_repo_sync(
                    await user_auth.get_user_id(),
                )

            if (
                self._should_attach(request)
                and not request.url.path.startswith('/api/email')
                and request.url.path
                not in ('/api/settings', '/api/logout', '/api/authenticate')
                and not user_auth.email_verified
            ):
                raise EmailNotVerifiedError

            return response
        except EmailNotVerifiedError as e:
            return JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_403_FORBIDDEN
            )
        except NoCredentialsError as e:
            logger.info(e.__class__.__name__)
            # The user is trying to use an expired token or has not logged in. No special event handling is required
            return JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_401_UNAUTHORIZED
            )
        except AuthError as e:
            logger.warning('auth_error', exc_info=True)
            try:
                await self._logout(request)
            except Exception as logout_error:
                logger.debug(str(logout_error))

            # Send a response that deletes the auth cookie if needed
            response = JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_401_UNAUTHORIZED
            )
            if keycloak_auth_cookie:
                response.delete_cookie(
                    key='keycloak_auth',
                    domain=get_cookie_domain(request),
                    samesite=get_cookie_samesite(request),
                )
            return response

    def _get_user_auth(self, request: Request) -> SaasUserAuth | None:
        return getattr(request.state, 'user_auth', None)

    def _check_tos(self, request: Request):
        keycloak_auth_cookie = request.cookies.get('keycloak_auth')
        auth_header = request.headers.get('Authorization')
        mcp_auth_header = request.headers.get('X-Session-API-Key')
        accepted_tos = False
        if (
            keycloak_auth_cookie is None
            and (auth_header is None or not auth_header.startswith('Bearer '))
            and mcp_auth_header is None
        ):
            raise NoCredentialsError

        jwt_secret: SecretStr = config.jwt_secret  # type: ignore[assignment]
        if keycloak_auth_cookie:
            try:
                decoded = jwt.decode(
                    keycloak_auth_cookie,
                    jwt_secret.get_secret_value(),
                    algorithms=['HS256'],
                )
                accepted_tos = decoded.get('accepted_tos')
            except jwt.exceptions.InvalidSignatureError:
                # If we can't decode the token, treat it as an auth error
                logger.warning('Invalid JWT signature detected')
                raise AuthError('Invalid authentication token')
            except Exception as e:
                # Handle any other JWT decoding errors
                logger.warning(f'JWT decode error: {str(e)}')
                raise AuthError('Invalid authentication token')
        else:
            # Don't fail an API call if the TOS has not been accepted.
            # The user will accept the TOS the next time they login.
            accepted_tos = True

        # TODO: This explicitly checks for "False" so it doesn't logout anyone
        # that has logged in prior to this change:
        # accepted_tos is "None" means the user has not re-logged in since this TOS change.
        # accepted_tos is "False" means the user was shown the TOS but has not accepted.
        # accepted_tos is "True" means the user has accepted the TOS
        #
        # Once the initial deploy is complete and every user has been logged out
        # after this change (12 hrs max), this should be changed to check
        # "if accepted_tos is not None" as there should not be any users with
        # accepted_tos equal to "None"
        if accepted_tos is False and request.url.path != '/api/accept_tos':
            logger.error('User has not accepted the terms of service')
            raise TosNotAcceptedError

    def _should_attach(self, request: Request) -> bool:
        if request.method == 'OPTIONS':
            return False
        path = request.url.path

        is_api_that_should_attach = path.startswith('/api') and path not in (
            '/api/options/config',
            '/api/keycloak/callback',
            '/api/billing/success',
            '/api/billing/cancel',
            '/api/billing/customer-setup-success',
            '/api/billing/stripe-webhook',
        )

        is_mcp = path.startswith('/mcp')
        return is_api_that_should_attach or is_mcp

    async def _logout(self, request: Request):
        # Log out of keycloak - this prevents issues where you did not log in with the idp you believe you used
        try:
            user_auth: SaasUserAuth = await get_user_auth(request)
            if user_auth and user_auth.refresh_token:
                await token_manager.logout(user_auth.refresh_token.get_secret_value())
        except Exception:
            logger.debug('Error logging out')


class LLMSettingsMiddleware:
    """Middleware to validate LLM settings access for enterprise users.

    Intercepts POST requests to /api/settings and validates that non-pro users
    cannot modify LLM-related settings.
    """

    async def __call__(self, request: Request, call_next: Callable):
        try:
            logger.warning(
                f'LLM middleware called for {request.method} {request.url.path}'
            )

            # Check if this is a POST request to /api/settings
            if request.method == 'POST' and request.url.path == '/api/settings':
                logger.warning('LLM middleware intercepting POST /api/settings request')
                await self._validate_llm_settings_request(request)

            # Continue with the request
            response: Response = await call_next(request)
            return response

        except HTTPException:
            # Re-raise HTTPException (our 403 response)
            raise
        except Exception as e:
            logger.warning(f'Error in LLM settings middleware: {e}')
            # Let other errors pass through to be handled by the route
            fallback_response: Response = await call_next(request)
            return fallback_response

    async def _validate_llm_settings_request(self, request: Request) -> None:
        """Validate LLM settings access for the current request."""
        try:
            logger.info(
                f"LLM settings middleware intercepting POST /api/settings from {request.client.host if request.client else 'unknown'}"
            )

            # Get user authentication - this will trigger authentication if not already done
            try:
                user_auth = await get_user_auth(request)
            except Exception as e:
                logger.info(f'No valid user auth found ({e}), letting route handle request')
                return  # No user auth, let the route handle it

            user_id = await user_auth.get_user_id()
            if not user_id:
                logger.info('No user ID found, letting route handle request')
                return  # No user ID, let the route handle it

            logger.info(f'Processing settings request for user: {user_id}')

            # Parse the request JSON to get new settings
            try:
                settings_data = await request.json()
                logger.info(f'Parsed settings data keys: {list(settings_data.keys())}')
            except Exception as e:
                logger.warning(f'Invalid JSON in request body: {e}')
                return  # Invalid JSON, let the route handle it

            # Convert to Settings object for validation
            try:
                new_settings = Settings(**settings_data)
                logger.info('Successfully created Settings object from request data')
            except Exception as e:
                logger.warning(f'Invalid settings format: {e}')
                return  # Invalid settings format, let the route handle it

            # Validate LLM settings access by comparing new settings against SaaS defaults
            await validate_llm_settings_access(user_id, new_settings)
            logger.info(f'LLM settings validation passed for user {user_id}')

        except HTTPException as e:
            logger.warning(
                f'LLM settings validation failed: HTTP {e.status_code} - {e.detail}'
            )
            # Re-raise our 403 response
            raise
        except Exception as e:
            logger.warning(f'Unexpected error validating LLM settings request: {e}')
            # Let other errors pass through


def _get_saas_default_settings() -> Settings:
    """Get the default SaaS settings for comparison."""
    return Settings(
        language='en',
        agent='CodeActAgent',
        enable_proactive_conversation_starters=True,
        enable_default_condenser=True,
        condenser_max_size=120,
        llm_model=get_default_litellm_model(),  # litellm_proxy/prod/claude-sonnet-4-20250514
        confirmation_mode=False,
        security_analyzer='llm',
        # Note: llm_api_key and llm_base_url are auto-provisioned for SaaS users,
        # so we don't include them in defaults - any custom values are changes
    )


def has_llm_settings_changes(user_settings: Settings, saas_defaults: Settings) -> bool:
    """Check if user settings contain changes to LLM-related settings from SaaS defaults."""
    logger.info(
        f"Checking LLM settings changes - User settings: {user_settings.model_dump(exclude={'secrets_store'})}"
    )
    logger.info(
        f"Checking LLM settings changes - SaaS defaults: {saas_defaults.model_dump(exclude={'secrets_store'})}"
    )

    # Core LLM settings - any custom values are changes since SaaS auto-provisions these
    if (
        user_settings.llm_model is not None
        and user_settings.llm_model != saas_defaults.llm_model
    ):
        logger.warning(
            f"LLM model change detected: user='{user_settings.llm_model}' vs default='{saas_defaults.llm_model}'"
        )
        return True
    if user_settings.llm_api_key is not None:
        # Any custom API key is a change (SaaS users get auto-provisioned keys)
        logger.warning(
            f'LLM API key change detected: user has custom key (length={len(user_settings.llm_api_key.get_secret_value()) if user_settings.llm_api_key else 0})'
        )
        return True
    if user_settings.llm_base_url is not None and user_settings.llm_base_url != '':
        # Any non-empty base URL is a change (SaaS users get auto-provisioned URL)
        logger.warning(
            f"LLM base URL change detected: user='{user_settings.llm_base_url}' (non-empty)"
        )
        return True

    # LLM-related configuration settings
    if user_settings.agent is not None and user_settings.agent != saas_defaults.agent:
        logger.warning(
            f"Agent change detected: user='{user_settings.agent}' vs default='{saas_defaults.agent}'"
        )
        return True
    if (
        user_settings.confirmation_mode is not None
        and user_settings.confirmation_mode != saas_defaults.confirmation_mode
    ):
        logger.warning(
            f'Confirmation mode change detected: user={user_settings.confirmation_mode} vs default={saas_defaults.confirmation_mode}'
        )
        return True
    if (
        user_settings.security_analyzer is not None
        and user_settings.security_analyzer != saas_defaults.security_analyzer
        and user_settings.security_analyzer != ''
    ):  # Handle empty string as None
        logger.warning(
            f"Security analyzer change detected: user='{user_settings.security_analyzer}' vs default='{saas_defaults.security_analyzer}'"
        )
        return True
    if user_settings.max_budget_per_task is not None:
        logger.warning(
            f'Max budget per task change detected: user={user_settings.max_budget_per_task}'
        )
        return True
    if user_settings.max_iterations is not None:
        logger.warning(
            f'Max iterations change detected: user={user_settings.max_iterations}'
        )
        return True

    # Memory/context management settings
    if user_settings.enable_default_condenser != saas_defaults.enable_default_condenser:
        logger.warning(
            f'Enable default condenser change detected: user={user_settings.enable_default_condenser} vs default={saas_defaults.enable_default_condenser}'
        )
        return True
    if (
        user_settings.condenser_max_size is not None
        and user_settings.condenser_max_size != saas_defaults.condenser_max_size
    ):
        logger.warning(
            f'Condenser max size change detected: user={user_settings.condenser_max_size} vs default={saas_defaults.condenser_max_size}'
        )
        return True

    logger.info('No LLM settings changes detected')
    return False


def _has_active_subscription(user_id: str) -> bool:
    """Check if user has an active subscription (pro user)."""
    with session_maker() as session:
        now = datetime.now(UTC)
        logger.info(f'Checking subscription for user {user_id} at time {now}')

        subscription_access = (
            session.query(SubscriptionAccess)
            .filter(SubscriptionAccess.status == 'ACTIVE')
            .filter(SubscriptionAccess.user_id == user_id)
            .filter(SubscriptionAccess.start_at <= now)
            .filter(SubscriptionAccess.end_at >= now)
            .first()
        )

        if subscription_access:
            logger.info(
                f'Found active subscription for user {user_id}: starts={subscription_access.start_at}, ends={subscription_access.end_at}'
            )
        else:
            logger.info(f'No active subscription found for user {user_id}')

        return subscription_access is not None


async def validate_llm_settings_access(
    user_id: str, user_settings: Settings, saas_defaults: Settings | None = None
) -> None:
    """Validate that user has permission to change LLM settings.

    Raises HTTPException with 403 status if non-pro user tries to change LLM settings.
    """
    if saas_defaults is None:
        saas_defaults = _get_saas_default_settings()

    logger.info(f'Validating LLM settings access for user: {user_id}')

    # Check if user is trying to change LLM settings
    if has_llm_settings_changes(user_settings, saas_defaults):
        logger.warning(f'User {user_id} attempting to change LLM settings')

        # Check if user has active subscription (is pro user)
        has_subscription = _has_active_subscription(user_id)
        logger.info(
            f"User {user_id} subscription status: {'active' if has_subscription else 'none'}"
        )

        if not has_subscription:
            logger.warning(
                f'Blocking non-pro user {user_id} from changing LLM settings'
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='LLM settings can only be modified by pro users',
            )
        else:
            logger.info(f'Allowing pro user {user_id} to change LLM settings')
    else:
        logger.info(f'User {user_id} making non-LLM settings changes only - allowing')
