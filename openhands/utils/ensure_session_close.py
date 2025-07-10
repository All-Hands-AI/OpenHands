"""
Session management utilities to handle unclosed HTTP sessions from LiteLLM and other libraries.

LiteLLM and other libraries have issues where HTTP sessions (both aiohttp and httpx) are created
but not properly closed, leading to resource leaks and "Unclosed client session" warnings.

This module provides context managers to monkey patch HTTP client classes and ensure
all sessions are properly closed when operations complete.
"""

import contextlib
import weakref

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


@contextlib.asynccontextmanager
async def ensure_aiohttp_close():
    """
    Context manager to ensure all aiohttp.ClientSession instances are properly closed.

    This patches aiohttp.ClientSession to track instances and ensures they are
    closed when the context exits.
    """
    if not AIOHTTP_AVAILABLE:
        yield
        return

    original_session_class = aiohttp.ClientSession
    sessions: weakref.WeakSet[aiohttp.ClientSession] = weakref.WeakSet()

    class SessionProxy(aiohttp.ClientSession):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sessions.add(self)

    # Monkey patch aiohttp.ClientSession
    aiohttp.ClientSession = SessionProxy

    try:
        yield
    finally:
        # Restore original class
        aiohttp.ClientSession = original_session_class

        # Close all tracked sessions
        for session in list(sessions):
            if not session.closed:
                await session.close()


@contextlib.contextmanager
def ensure_httpx_close():
    """
    Context manager to ensure all httpx.Client instances are properly closed.

    This is based on the existing implementation but enhanced for reliability.
    """
    if not HTTPX_AVAILABLE:
        yield
        return

    wrapped_class = httpx.Client
    proxies = []

    class ClientProxy:
        """
        Proxy for httpx.Client that ensures proper cleanup.
        """

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.client = wrapped_class(*self.args, **self.kwargs)
            proxies.append(self)

        def __getattr__(self, name):
            if self.client is None:
                self.client = wrapped_class(*self.args, **self.kwargs)
            return getattr(self.client, name)

        def close(self):
            if self.client:
                self.client.close()
                self.client = None

        def __iter__(self, *args, **kwargs):
            if self.client:
                return self.client.iter(*args, **kwargs)
            return object.__getattribute__(self, 'iter')(*args, **kwargs)

        @property
        def is_closed(self):
            if self.client is None:
                return True
            return self.client.is_closed

    httpx.Client = ClientProxy
    try:
        yield
    finally:
        httpx.Client = wrapped_class
        while proxies:
            proxy = proxies.pop()
            proxy.close()


@contextlib.asynccontextmanager
async def ensure_all_sessions_close():
    """
    Context manager that ensures both aiohttp and httpx sessions are properly closed.

    This should be used around operations that might create HTTP sessions through
    LiteLLM or other libraries.
    """
    async with ensure_aiohttp_close():
        with ensure_httpx_close():
            yield
