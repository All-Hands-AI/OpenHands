from fastapi import APIRouter

from openhands.server.routes.integration.conversation import conversation_router
from openhands.server.routes.integration.space import space_router

app = APIRouter(prefix='/api/v1/integration')

app.include_router(conversation_router, tags=['conversations'])
app.include_router(space_router, tags=['spaces'])
