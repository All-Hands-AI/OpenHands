from a2a.server.apps import A2AFastAPIApplication

from openhands.server.a2a.a2a_request_handler import A2aRequestHandler
from openhands.server.a2a.agent_card import agent_card

request_handler = A2aRequestHandler()

jsonrpc_app = A2AFastAPIApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

fastapi_app = jsonrpc_app.build(
    agent_card_url = '/.well-known/agent.json',
    rpc_url = '/a2a',
)

app = fastapi_app.router
