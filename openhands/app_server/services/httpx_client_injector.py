from typing import AsyncGenerator

import httpx
from fastapi import Request
from pydantic import BaseModel, Field

from openhands.app_server.services.injector import Injector, InjectorState


class HttpxClientInjector(BaseModel, Injector[httpx.AsyncClient]):
    """Injector for a httpx client. By keeping a single httpx client alive in the
    context of server requests handshakes are minimized while connection pool leaks
    are prevented."""

    timeout: int = Field(default=15, description='Default timeout on all http requests')

    async def inject(
        self, state: InjectorState, request: Request | None = None
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        httpx_client = getattr(state, 'httpx_client', None)
        if not httpx_client:
            httpx_client = httpx.AsyncClient(timeout=self.timeout)
            setattr(state, 'httpx_client', httpx_client)
        yield httpx_client
