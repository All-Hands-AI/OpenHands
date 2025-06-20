from a2a.server.apps import A2AStarletteApplication

from openhands.server.a2a.a2a_request_handler import A2aRequestHandler
from openhands.server.a2a.agent_card import agent_card

request_handler = A2aRequestHandler()

server = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

app = server.build()
