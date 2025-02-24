"""
LiteLLM currently have an issue where HttpHandlers are being created but not
closed. We have submitted a PR to them, (https://github.com/BerriAI/litellm/pull/8711)
and their dev team say they are in the process of a refactor that will fix this, but
in the meantime, we need to manage the lifecycle of the httpx.Client manually.

We can't simply pass in our own client object, because all the different implementations use
different types of client object.

So we monkey patch the httpx.Client class to track newly created instances and close these
when the operations complete. (This is relatively safe, as if the client is reused after this
then is will transparently reopen)

Hopefully, this will be fixed soon and we can remove this abomination.
"""

from dataclasses import dataclass, field
from functools import wraps
from typing import Callable

from httpx import Client


@dataclass
class EnsureHttpxClose:
    clients: list[Client] = field(default_factory=list)
    original_init: Callable | None = None

    def __enter__(self):
        self.original_init = Client.__init__

        @wraps(Client.__init__)
        def init_wrapper(*args, **kwargs):
            self.clients.append(args[0])
            return self.original_init(*args, **kwargs)  # type: ignore

        Client.__init__ = init_wrapper

    def __exit__(self, type, value, traceback):
        Client.__init__ = self.original_init
        while self.clients:
            client = self.clients.pop()
            client.close()
