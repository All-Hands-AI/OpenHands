import asyncio
import uuid
from abc import ABC
from typing import AsyncGenerator, List

from openhands.a2a.client.card_resolver import A2ACardResolver
from openhands.a2a.client.client import A2AClient
from openhands.a2a.common.types import (
    A2AClientHTTPError,
    A2AClientJSONError,
    AgentCard,
    Message,
    SendTaskResponse,
    SendTaskStreamingResponse,
    TaskSendParams,
    TextPart,
)
from openhands.core.logger import openhands_logger as logger


class A2AManager(ABC):
    list_remote_agent_servers: List[str] = []
    list_remote_agent_cards: dict[str, AgentCard] = {}

    def __init__(self, a2a_server_urls: List[str]):
        self.list_remote_agent_servers = a2a_server_urls
        self.list_remote_agent_cards = {}

    def register_remote_card(self, agent_card: AgentCard):
        self.list_remote_agent_cards[agent_card.name] = agent_card

    async def initialize_agent_cards(self):
        if not self.list_remote_agent_servers:
            return

        async def fetch_card(server_url: str) -> AgentCard:
            async with A2ACardResolver(server_url) as resolver:
                try:
                    return await resolver.get_agent_card()
                except (A2AClientHTTPError, A2AClientJSONError) as e:
                    print(f'Failed to fetch agent card from {server_url}: {str(e)}')
                    return None

        tasks = [fetch_card(server) for server in self.list_remote_agent_servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for card in results:
            if card is not None:
                logger.info(f'Registered remote agent card: {card.name}')
                self.list_remote_agent_cards[card.name] = card

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.list_remote_agent_cards:
            return []
        remote_agent_info = []
        for card in self.list_remote_agent_cards.values():
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

    async def send_task(
        self, agent_name: str, message: str, sid: str
    ) -> AsyncGenerator[SendTaskStreamingResponse | SendTaskResponse, None]:
        """Send a task to a remote agent and yield task responses.

        Args:
            agent_name: Name of the remote agent
            message: Message to send to the agent
            sid: Session ID

        Yields:
            TaskStatusUpdateEvent or Task: Task response updates
        """
        if agent_name not in self.list_remote_agent_cards:
            raise ValueError(f'Agent {agent_name} not found')

        card = self.list_remote_agent_cards[agent_name]
        client = A2AClient(card)
        request: TaskSendParams = TaskSendParams(
            id=str(uuid.uuid4()),
            sessionId=sid,
            message=Message(
                role='user',
                parts=[TextPart(text=message)],
                metadata={},
            ),
            acceptedOutputModes=['text', 'text/plain', 'image/png'],
            metadata={'conversation_id': sid},
        )

        if card.capabilities.streaming:
            async for response in client.send_task_streaming(request):
                yield response
        else:
            response = await client.send_task(request)
            yield response

    @classmethod
    def from_toml_config(cls, config: dict) -> 'A2AManager':
        a2a_manager = cls(config['a2a_server_url'])
        return a2a_manager
