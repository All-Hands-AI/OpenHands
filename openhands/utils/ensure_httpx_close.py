"""
LiteLLM currently have an issue where HttpHandlers are being created but not
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
from typing import Any, Callable, Iterator, Optional, cast

import httpx


@contextlib.contextmanager
def ensure_httpx_close() -> Iterator[None]:
    wrapped_class = httpx.Client
    proxys: list['ClientProxy'] = []

    class ClientProxy:
        """
        Sometimes LiteLLM opens a new httpx client for each connection, and does not close them.
        Sometimes it does close them. Sometimes, it reuses a client between connections. For cases
        where a client is reused, we need to be able to reuse the client even after closing it.
        """

        client_constructor: Callable
        args: tuple
        kwargs: dict
        client: Optional[httpx.Client]

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs
            self.client = wrapped_class(*self.args, **self.kwargs)
            proxys.append(self)

        def __getattr__(self, name: str) -> Any:
            # Invoke a method on the proxied client - create one if required
            if self.client is None:
                self.client = wrapped_class(*self.args, **self.kwargs)
            return getattr(self.client, name)

        def close(self) -> None:
            # Close the client if it is open
            if self.client:
                self.client.close()
                self.client = None

        def __iter__(self, *args: Any, **kwargs: Any) -> Any:
            # We have to override this as debuggers invoke it causing the client to reopen
            if self.client:
                # Use getattr instead of direct attribute access to avoid mypy error
                iter_method = getattr(self.client, 'iter', None)
                if iter_method:
                    return iter_method(*args, **kwargs)
            return object.__getattribute__(self, 'iter')(*args, **kwargs)

        @property
        def is_closed(self) -> bool:
            # Check if closed
            if self.client is None:
                return True
            # Cast to bool to avoid mypy error
            return bool(self.client.is_closed)

    # Use a variable to hold the original class to avoid mypy error
    original_client = httpx.Client
    # We need to monkey patch the httpx.Client class
    # Using globals() to avoid mypy errors about assigning to a type
    # mypy: disable-error-code="misc"
    globals()['httpx'].Client = cast(type[httpx.Client], ClientProxy)
    try:
        yield
    finally:
        # Restore the original class
        # mypy: disable-error-code="misc"
        globals()['httpx'].Client = original_client
        while proxys:
            proxy = proxys.pop()
            proxy.close()
