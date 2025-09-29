"""FastAPI application for OpenHands Server."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import APIRouter, FastAPI

from openhands.agent_server.middleware import LocalhostCORSMiddleware
from openhands.app_server.config import get_global_config
from openhands.app_server.database import create_tables, drop_tables
from openhands.app_server.event import event_router
from openhands.app_server.event_callback import (
    event_webhook_router,
)
from openhands.app_server.sandbox import sandbox_router, sandbox_spec_router

# from openhands.app_server.sandboxed_conversation import sandboxed_conversation_router
from openhands.app_server.user import user_router

_config = get_global_config()

# TODO: This will need to die. :(


@asynccontextmanager
async def _api_lifespan(api: FastAPI) -> AsyncIterator[None]:
    # TODO: Replace this with an invocation of the alembic migrations
    await create_tables()
    yield
    await drop_tables()


api = FastAPI(
    title='OpenHands App Server',
    description=(
        'Management Server for multiple Sandboxed OpenHands Agent Server Instances'
    ),
    version='0.1.0',
    lifespan=_api_lifespan,
)

# Add CORS middleware
api.add_middleware(LocalhostCORSMiddleware, allow_origins=_config.allow_cors_origins)

# Include routers
api_router = APIRouter(prefix='/api')
api_router.include_router(event_router.router)
# api_router.include_router(sandboxed_conversation_router.router)
api_router.include_router(sandbox_router.router)
api_router.include_router(sandbox_spec_router.router)
api_router.include_router(user_router.router)
api.include_router(api_router)
api.include_router(event_webhook_router.router)


@api.get('/')
async def root():
    """Root endpoint."""
    return {
        'title': 'OpenHands App Server',
        'version': '0.1.0',
        'docs': '/docs',
        'redoc': '/redoc',
    }
