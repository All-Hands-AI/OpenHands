import json
from typing import Optional

import httpx

from openhands.a2a.common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    AgentCard,
)


class A2ACardResolver:
    def __init__(self, base_url: str, agent_card_path: str = '/.well-known/agent.json'):
        self.base_url = base_url.rstrip('/')
        self.agent_card_path = agent_card_path.lstrip('/')
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_agent_card(self) -> AgentCard:
        if not self._client:
            self._client = httpx.AsyncClient()

        try:
            response = await self._client.get(
                self.base_url + '/' + self.agent_card_path
            )
            response.raise_for_status()
            try:
                return AgentCard(**response.json())
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(
                    f'Failed to parse agent card JSON: {str(e)}'
                ) from e
        except httpx.RequestError as e:
            raise A2AClientHTTPError(
                400, f'Failed to fetch agent card: {str(e)}'
            ) from e
        except httpx.HTTPStatusError as e:
            raise A2AClientHTTPError(
                e.response.status_code, f'HTTP error occurred: {str(e)}'
            ) from e
