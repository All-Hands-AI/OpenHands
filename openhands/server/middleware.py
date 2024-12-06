import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable
from urllib.parse import urlparse

import jwt
from fastapi import APIRouter, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from openhands.core.logger import openhands_logger as logger
from openhands.server.auth import get_sid_from_token
from openhands.server.github_utils import UserVerifier
from openhands.server.shared import config, session_manager


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


class NoCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to disable caching for all routes by adding appropriate headers
    """

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith('/assets'):
            response.headers['Cache-Control'] = (
                'no-cache, no-store, must-revalidate, max-age=0'
            )
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response


class InMemoryRateLimiter:
    history: dict
    requests: int
    seconds: int
    sleep_seconds: int

    def __init__(self, requests: int = 2, seconds: int = 1, sleep_seconds: int = 1):
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

    async def dispatch(self, request, call_next):
        ok = await self.rate_limiter(request)
        if not ok:
            return JSONResponse(
                status_code=429,
                content={'message': 'Too many requests'},
                headers={'Retry-After': '1'},
            )
        return await call_next(request)


class AttachSessionMiddleware:
    def __init__(self, app, target_router: APIRouter):
        self.app = app
        self.target_router = target_router
        self.target_paths = {route.path for route in target_router.routes}

    async def __call__(self, request: Request, call_next: Callable):
        do_attach = False
        if request.url.path in self.target_paths:
            do_attach = True

        if request.method == 'OPTIONS':
            do_attach = False

        if not do_attach:
            return await call_next(request)

        user_verifier = UserVerifier()
        if user_verifier.is_active():
            signed_token = request.cookies.get('github_auth')
            if not signed_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'error': 'Not authenticated'},
                )
            try:
                jwt.decode(signed_token, config.jwt_secret, algorithms=['HS256'])
            except Exception as e:
                logger.warning(f'Invalid token: {e}')
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={'error': 'Invalid token'},
                )

        if not request.headers.get('Authorization'):
            logger.warning('Missing Authorization header')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Missing Authorization header'},
            )

        auth_token = request.headers.get('Authorization')
        if 'Bearer' in auth_token:
            auth_token = auth_token.split('Bearer')[1].strip()

        request.state.sid = get_sid_from_token(auth_token, config.jwt_secret)
        if request.state.sid == '':
            logger.warning('Invalid token')
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={'error': 'Invalid token'},
            )

        request.state.conversation = await session_manager.attach_to_conversation(
            request.state.sid
        )
        if request.state.conversation is None:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Session not found'},
            )
        try:
            response = await call_next(request)
        finally:
            await session_manager.detach_from_conversation(request.state.conversation)
        return response
