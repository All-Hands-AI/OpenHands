import httpx
from pydantic import BaseModel, Field, PrivateAttr


class HttpxClientManager(BaseModel):
    timeout: int = Field(default=15, description="Default timeout on all http requests")
    _httpx_client: httpx.AsyncClient | None = PrivateAttr(default=None)

    def get_httpx_client(self) -> httpx.AsyncClient:
        httpx_client = self._httpx_client
        if httpx_client is None:
            httpx_client = httpx.AsyncClient(timeout=self.timeout)
            self._httpx_client = httpx_client
        return httpx_client
