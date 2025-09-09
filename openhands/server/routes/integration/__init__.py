from fastapi import APIRouter

from openhands.server.routes.integration.conversation import (
    chat_router,
    conversation_router,
    deep_research_router,
)
from openhands.server.routes.integration.space import space_router

app = APIRouter(prefix='/api/v1/integration')

app.include_router(conversation_router, tags=['conversations'])
app.include_router(space_router, tags=['spaces'])
app.include_router(chat_router, tags=['conversations'])
app.include_router(deep_research_router, tags=['conversations'])
