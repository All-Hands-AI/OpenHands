import asyncio
import collections
import time
from typing import Callable, Dict, Optional
from urllib.parse import urlparse

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


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


class InMemoryStore:
    """Thread-safe in-memory store for rate limiting."""

    def __init__(self):
        self.storage: Dict[str, collections.deque] = {}
        self._lock = asyncio.Lock()

    async def incr(self, key: str) -> int:
        """Increment the counter for a key and return the new count.

        Args:
            key (str): The key to increment.

        Returns:
            int: The new count after incrementing.
        """
        async with self._lock:
            if key not in self.storage:
                self.storage[key] = collections.deque()
            now = time.time()
            self.storage[key].append(now)
            return len(self.storage[key])

    async def expire(self, key: str, seconds: int) -> None:
        """Remove expired entries for a key.

        Args:
            key (str): The key to check.
            seconds (int): The expiration time in seconds.
        """
        async with self._lock:
            if key not in self.storage:
                return
            now = time.time()
            while self.storage[key] and self.storage[key][0] < now - seconds:
                self.storage[key].popleft()

    async def get(self, key: str) -> Optional[int]:
        """Get the current count for a key.

        Args:
            key (str): The key to get.

        Returns:
            Optional[int]: The current count, or None if the key doesn't exist.
        """
        async with self._lock:
            if key not in self.storage:
                return None
            return len(self.storage[key])


class RateLimiter:
    """Rate limiter middleware that uses a sliding window algorithm.

    This implementation uses an in-memory store to track request counts
    per client IP and path. It uses a sliding window to ensure accurate
    rate limiting even at window boundaries.
    """

    def __init__(self, times: int = 1, seconds: int = 1):
        """Initialize the rate limiter.

        Args:
            times (int, optional): Number of requests allowed. Defaults to 1.
            seconds (int, optional): Time window in seconds. Defaults to 1.
        """
        self.times = times
        self.seconds = seconds
        self.store = store

    def _get_key(self, scope: dict) -> str:
        """Generate a unique key for rate limiting based on client IP and path.

        Args:
            scope (dict): The ASGI scope dictionary.

        Returns:
            str: A unique key combining client IP and path.
        """
        # Use client's IP address as the key
        client = scope.get('client', ['127.0.0.1'])[0]
        path = scope.get('path', '')
        return f'rate_limit:{client}:{path}'

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Apply rate limiting to the request.

        Args:
            scope (dict): The ASGI scope dictionary.
            receive (Callable): The ASGI receive function.
            send (Callable): The ASGI send function.
        """
        key = self._get_key(scope)
        await self.store.expire(key, self.seconds)
        requests = await self.store.get(key) or 0
        if requests >= self.times:
            await send(
                {
                    'type': 'http.response.start',
                    'status': 429,
                    'headers': [(b'content-type', b'text/plain')],
                }
            )
            await send(
                {
                    'type': 'http.response.body',
                    'body': b'Too many requests',
                }
            )
            return
        await self.store.incr(key)


store = InMemoryStore()
