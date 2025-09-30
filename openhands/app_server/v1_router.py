from fastapi import APIRouter

from openhands.app_server.event import event_router
from openhands.app_server.event_callback import (
    event_webhook_router,
)
from openhands.app_server.sandbox import sandbox_router, sandbox_spec_router
from openhands.app_server.user import user_router

# Include routers
router = APIRouter(prefix='/v1')
router.include_router(event_router.router)
# api_router.include_router(sandboxed_conversation_router.router)
router.include_router(sandbox_router.router)
router.include_router(sandbox_spec_router.router)
router.include_router(user_router.router)
router.include_router(event_webhook_router.router)
