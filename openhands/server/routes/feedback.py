from fastapi import APIRouter
from openhands.server.dependencies import get_dependencies

app = APIRouter(prefix='/api/conversations/{conversation_id}', dependencies=get_dependencies())

# Feedback functionality has been removed
