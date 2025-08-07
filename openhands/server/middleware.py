import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.types import ASGIApp

from openhands.core.logger import openhands_logger as logger
from openhands.server import shared
from openhands.server.auth import get_user_id
from openhands.server.modules.conversation import conversation_module
from openhands.server.thesis_auth import (
    ThesisUser,
    get_user_detail_by_api_key,
    get_user_detail_from_thesis_auth_server,
)
from openhands.server.types import SessionMiddlewareInterface
from openhands.server.utils.ratelimit_storage import (
    InMemoryRateLimiterStorage,
    RateLimiterStorage,
)


def is_integration_api(request: Request) -> bool:
    return request.url.path.startswith('/api/v1/integration')


class LocalhostCORSMiddleware(CORSMiddleware):
    """
    Custom CORS middleware that allows any request from localhost/127.0.0.1 domains,
    while using standard CORS rules for other origins.
    """

    def __init__(self, app: ASGIApp, **kwargs) -> None:
        super().__init__(app, **kwargs)

    def is_allowed_origin(self, origin: str) -> bool:
        if origin:
            parsed = urlparse(origin)
            hostname = parsed.hostname or ''

            # Allow any localhost/127.0.0.1 origin regardless of port
            if hostname in ['localhost', '127.0.0.1']:
                return True

        # For missing origin or other origins, use the parent class's logic
        return super().is_allowed_origin(origin)


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware to disable caching for all routes by adding appropriate headers
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith('/assets'):
            # The content of the assets directory has fingerprinted file names so we cache aggressively
            response.headers['Cache-Control'] = 'public, max-age=2592000, immutable'
        else:
            response.headers['Cache-Control'] = (
                'no-cache, no-store, must-revalidate, max-age=0'
            )
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


class InMemoryRateLimiter:
    history: dict
    requests: int
    seconds: float
    sleep_seconds: float

    def __init__(self, requests: int = 2, seconds: float = 1, sleep_seconds: float = 1):
        self.requests = requests
        self.seconds = seconds
        self.sleep_seconds = sleep_seconds
        self.history = defaultdict(list)
        self.sleep_seconds = sleep_seconds

    def _clean_old_requests(self, key: str) -> None:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.seconds)
        self.history[key] = [ts for ts in self.history[key] if ts > cutoff]

    async def __call__(self, request: Request) -> bool:
        if request.client is None:
            return True
        key = request.client.host
        now = datetime.now()

        self._clean_old_requests(key)

        self.history[key].append(now)

        if len(self.history[key]) > self.requests * 2:
            return False
        elif len(self.history[key]) > self.requests:
            if self.sleep_seconds > 0:
                await asyncio.sleep(self.sleep_seconds)
                return True
            else:
                return False

        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, rate_limiter: InMemoryRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: StarletteRequest, call_next):
        if not self.is_rate_limited_request(request):
            return await call_next(request)
        ok = await self.rate_limiter(request)
        if not ok:
            return JSONResponse(
                status_code=429,
                content={'message': 'Too many requests'},
                headers={'Retry-After': '1'},
            )
        return await call_next(request)

    def is_rate_limited_request(self, request: StarletteRequest):
        if request.url.path.startswith('/assets'):
            return False
        # Put Other non rate limited checks here
        return True


class UserBasedRateLimiter:
    """Rate limiter that tracks requests per user ID extracted from access tokens."""

    def __init__(
        self,
        requests: int = 60,
        seconds: float = 60,
        sleep_seconds: float = 1,
        storage: RateLimiterStorage | None = None,
    ):
        """
        Initialize the rate limiter.

        Args:
            requests: Maximum number of requests allowed
            seconds: Time window for the rate limit
            sleep_seconds: Seconds to sleep when rate limit is exceeded (0 to reject immediately)
            storage: Storage backend to use (if None, will use in-memory storage)
        """
        self.requests = requests
        self.seconds = seconds
        self.sleep_seconds = sleep_seconds
        self.storage = storage or InMemoryRateLimiterStorage()

    async def is_allowed(self, user_id: str) -> bool:
        """
        Check if the user is allowed to make a request.

        Args:
            user_id: The user ID to check rate limit for

        Returns:
            True if request is allowed, False otherwise
        """
        if not user_id:
            return False

        now = datetime.now()
        cutoff = now - timedelta(seconds=self.seconds)

        try:
            # Clean old requests
            await self.storage.clean_old_requests(user_id, cutoff)

            # Add current request
            await self.storage.add_request(user_id, now)

            # Check if over the limit
            request_count = await self.storage.get_request_count(user_id)

            if request_count > self.requests * 2:
                return False
            elif request_count > self.requests:
                if self.sleep_seconds > 0:
                    await asyncio.sleep(self.sleep_seconds)
                    return True
                else:
                    return False

            return True
        except Exception as e:
            logger.error(f'Storage error in rate limiter for user {user_id}: {e}')
            # In case of storage errors, default to allowing the request
            # This prevents storage failures from blocking all traffic
            return True


class IntegrationRateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply user-based rate limiting to integration API routes."""

    def __init__(self, app, rate_limiter: UserBasedRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Only apply rate limiting to integration API routes
        if not is_integration_api(request):
            return await call_next(request)

        # Get user ID from request state (set by JWT middleware)
        try:
            user_id = (
                getattr(request.state, 'user_id', None)
                if hasattr(request, 'state')
                else None
            )
        except AttributeError:
            user_id = None

        if not user_id:
            logger.warning('No user_id found in request state for integration API')
            return JSONResponse(
                status_code=401,
                content={'detail': 'Authentication required'},
            )

        # Check rate limit
        is_allowed = await self.rate_limiter.is_allowed(user_id)

        if not is_allowed:
            logger.warning(f'Rate limit exceeded for user {user_id}')
            return JSONResponse(
                status_code=429,
                content={
                    'detail': 'Rate limit exceeded. Too many requests from this user.',
                    'retry_after': self.rate_limiter.seconds,
                },
                headers={'Retry-After': str(self.rate_limiter.seconds)},
            )

        return await call_next(request)


class AttachConversationMiddleware(SessionMiddlewareInterface):
    def __init__(self, app):
        self.app = app

    def _should_attach(self, request) -> bool:
        """
        Determine if the middleware should attach a session for the given request.
        """
        if request.method == 'OPTIONS':
            return False

        conversation_id = ''
        if request.url.path.startswith('/api/conversation'):
            # FIXME: we should be able to use path_params
            path_parts = request.url.path.split('/')
            if len(path_parts) > 0 and path_parts[-1] == 'visibility':
                return False
            if len(path_parts) > 4:
                conversation_id = request.url.path.split('/')[3]
        if request.url.path.startswith('/api/v1/integration/conversations'):
            path_parts = request.url.path.split('/')
            if len(path_parts) >= 6:
                conversation_id = request.url.path.split('/')[5]
        if not conversation_id:
            return False

        request.state.sid = conversation_id

        return True

    async def _attach_conversation(self, request: Request) -> JSONResponse | None:
        """
        Attach the user's session based on the provided authentication token.
        """
        request.state.conversation = (
            await shared.conversation_manager.attach_to_conversation(
                request.state.sid, get_user_id(request)
            )
        )
        if not request.state.conversation:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Session not found'},
            )
        return None

    async def _detach_session(self, request: Request) -> None:
        """
        Detach the user's session.
        """
        await shared.conversation_manager.detach_from_conversation(
            request.state.conversation
        )

    async def __call__(self, request: Request, call_next: Callable):
        if not self._should_attach(request):
            return await call_next(request)

        response = await self._attach_conversation(request)
        if response:
            return response

        try:
            # Continue processing the request
            response = await call_next(request)
        finally:
            # Ensure the session is detached
            await self._detach_session(request)

        return response


class ProviderTokenMiddleware(SessionMiddlewareInterface):
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next: Callable):
        settings_store = await shared.SettingsStoreImpl.get_instance(
            shared.config, get_user_id(request)
        )
        settings = await settings_store.load()

        # TODO: To avoid checks like this we should re-add the abilty to have completely different middleware in SAAS as in OSS
        if getattr(request.state, 'provider_tokens', None) is None:
            if (
                settings
                and settings.secrets_store
                and settings.secrets_store.provider_tokens
            ):
                request.state.provider_tokens = settings.secrets_store.provider_tokens
            else:
                request.state.provider_tokens = None

        return await call_next(request)


class CheckUserActivationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_paths = [
            '/api/auth/signup',
            '/alive',
            '/server_info',
            '/api/options/config',
            '/api/options/models',
            '/api/options/agents',
            '/api/options/security-analyzers',
            '/api/options/use-cases',
            '/api/options/use-cases/conversations',
            '/api/options/update-empty-titles',
            '/api/options/conversations',
            '/api/invitation/',
            '/api/user/status',
            '/api/invitation/validate',
            '/api/usecases',
            '/docs',
            '/openapi.json',
        ]

        self.public_path_patterns = [
            '/api/options/use-cases/conversations/',
            '/api/options/conversations/events/',
            '/api/options/conversations/list-files-internal/',
            '/api/options/conversations/select-file-internal/',
        ]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths:
            return await call_next(request)
        for pattern in self.public_path_patterns:
            if request.url.path.startswith(pattern):
                remaining = request.url.path[len(pattern) :]
                if remaining and '/' not in remaining:
                    return await call_next(request)

        if '/api/conversations/' in request.url.path:
            path_parts = request.url.path.split('/')

            # Bypass authentication for visibility endpoints
            if len(path_parts) > 0 and path_parts[-1] == 'visibility':
                return await call_next(request)
            if (
                request.state
                and hasattr(request.state, 'user_id')
                and hasattr(request.state, 'sid')
            ):
                if request.state.user_id and request.state.sid:
                    return await call_next(request)

        user_id = get_user_id(request)
        logger.info(f'Checking user activation for {user_id}')
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'User not authenticated'},
            )

        user = request.state.user

        if not user:
            return JSONResponse(
                status_code=404,
                content={'detail': 'User not found'},
            )

        # if user.whitelisted != UserStatus.WHITELISTED:
        #     return JSONResponse(
        #         status_code=403,
        #         content={'detail': 'User account is not activated'},
        #     )
        return await call_next(request)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_paths = [
            '/api/auth/signup',
            '/alive',
            '/server_info',
            '/api/options/config',
            '/api/options/models',
            '/api/options/agents',
            '/api/options/security-analyzers',
            '/api/options/use-cases',
            '/api/options/use-cases/conversations',
            '/api/options/conversations',
            '/api/options/update-empty-titles',
            '/api/usecases',
            '/docs',
            '/openapi.json',
        ]

        self.public_path_patterns = [
            '/api/options/use-cases/conversations/',
            '/api/options/conversations/events/',
            '/api/options/conversations/list-files-internal/',
            '/api/options/conversations/select-file-internal/',
        ]

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths:
            return await call_next(request)

        if is_integration_api(request):
            return await call_next(request)

        for pattern in self.public_path_patterns:
            if request.url.path.startswith(pattern):
                remaining = request.url.path[len(pattern) :]
                if remaining and '/' not in remaining:
                    return await call_next(request)
        if '/api/conversations/' in request.url.path:
            path_parts = request.url.path.split('/')

            # Bypass authentication for visibility endpoints
            if len(path_parts) > 0 and path_parts[-1] == 'visibility':
                return await call_next(request)

            conversation_index = path_parts.index('conversations')
            if len(path_parts) > conversation_index + 1:
                conversation_id = path_parts[conversation_index + 1]
                # Check if the conversation is public
                (
                    error,
                    visibility_info,
                ) = await conversation_module._get_conversation_visibility_info(
                    conversation_id
                )
                if error is None:
                    request.state.sid = conversation_id
                    request.state.user_id = visibility_info['user_id']
                    return await call_next(request)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'Missing or invalid authorization header'},
            )

        # token = auth_header.split(' ')[1]
        try:
            user: ThesisUser | None = await get_user_detail_from_thesis_auth_server(
                request.headers.get('Authorization'),
                request.headers.get('x-device-id'),
            )
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={'detail': 'User not found'},
                )
            user_id = user.publicAddress
            # Only set user in request.state if all checks pass
            request.state.user_id = user_id
            request.state.user = user

            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={'detail': e.detail},
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'detail': 'Internal server error'},
            )


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not is_integration_api(request):
            return await call_next(request)

        auth_header = request.headers.get('Authorization')
        api_key = auth_header.split(' ')[-1]
        if not auth_header or not auth_header.startswith('Bearer ') or not api_key:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'detail': 'Missing or invalid authorization header'},
            )

        try:
            user, access_token = await get_user_detail_by_api_key(api_key)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'detail': 'Invalid API key'},
                )
            user_id = user.publicAddress
            # Only set user in request.state if all checks pass
            request.state.user_id = user_id
            request.state.user = user
            request.state.access_token = access_token

            # replace header Authorization with Bearer token
            new_headers = []
            for header, value in request.scope['headers']:
                if header.lower() != b'authorization':
                    new_headers.append((header, value))
                    continue
                new_headers.append((header, f'Bearer {access_token}'.encode()))
            request.scope['headers'] = new_headers
            request.headers._list = new_headers

            return await call_next(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={'detail': e.detail},
            )
