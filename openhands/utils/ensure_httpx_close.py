"""LiteLLM currently have an issue where HttpHandlers are being created but not
closed. We have submitted a PR to them, (https://github.com/BerriAI/litellm/pull/8711)
and their dev team say they are in the process of a refactor that will fix this, but
in the meantime, we need to manage the lifecycle of the httpx.Client manually.

We can't simply pass in our own client object, because all the different implementations use
different types of client object.

So we monkey patch the httpx.Client class to track newly created instances and close these
when the operations complete. (Since some paths create a single shared client and reuse these,
we actually need to create a proxy object that allows these clients to be reusable.)

Hopefully, this will be fixed soon and we can remove this abomination.
"""

import contextlib
from typing import Callable

import httpx


@contextlib.contextmanager
def ensure_httpx_close():
    wrapped_class = httpx.Client
    proxys = []

    class ClientProxy:
        """Sometimes LiteLLM opens a new httpx client for each connection, and does not close them.
        Sometimes it does close them. Sometimes, it reuses a client between connections. For cases
        where a client is reused, we need to be able to reuse the client even after closing it.
        """

        client_constructor: Callable
        args: tuple
        kwargs: dict
        client: httpx.Client

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.client = wrapped_class(*self.args, **self.kwargs)
            proxys.append(self)

        def __getattr__(self, name):
            # Invoke a method on the proxied client - create one if required
            if self.client is None:
                self.client = wrapped_class(*self.args, **self.kwargs)
            return getattr(self.client, name)

        def close(self):
            # Close the client if it is open
            if self.client:
                self.client.close()
                self.client = None

        def __iter__(self, *args, **kwargs):
            # We have to override this as debuggers invoke it causing the client to reopen
            if self.client:
                return self.client.iter(*args, **kwargs)
            return object.__getattribute__(self, 'iter')(*args, **kwargs)

        @property
        def is_closed(self):
            # Check if closed
            if self.client is None:
                return True
            return self.client.is_closed

    httpx.Client = ClientProxy
    try:
        yield
    finally:
        httpx.Client = wrapped_class
        while proxys:
            proxy = proxys.pop()
            proxy.close()
