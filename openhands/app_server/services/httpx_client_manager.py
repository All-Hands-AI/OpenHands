from typing import AsyncGenerator

import httpx
from fastapi import Request
from pydantic import BaseModel, Field


class HttpxClientManager(BaseModel):
    timeout: int = Field(default=15, description='Default timeout on all http requests')

    async def resolve(
        self, request: Request
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Sharing a single client in the system can save time on handshakes, but leave us
        susceptible to leaks. Opening a different httpx connection for each operation is inefficient.
        So the balance is a managed connection shared within a fastapi request
        """
        httpx_client = getattr(request.state, 'httpx_client', None)
        if not httpx_client:
            httpx_client = httpx.AsyncClient(timeout=self.timeout)
            request.state.httpx_client = httpx_client
        yield httpx_client
