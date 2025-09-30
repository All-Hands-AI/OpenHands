"""FastAPI application for OpenHands Server."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from openhands.agent_server.middleware import LocalhostCORSMiddleware
from openhands.app_server import v1_router
from openhands.app_server.config import get_global_config
from openhands.app_server.database import create_tables

_config = get_global_config()


@asynccontextmanager
async def _api_lifespan(api: FastAPI) -> AsyncIterator[None]:
    # TODO: Replace this with an invocation of the alembic migrations
    await create_tables()
    yield


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
api.include_router(v1_router.router)


@api.get('/')
async def root():
    """Root endpoint."""
    return {
        'title': 'OpenHands App Server',
        'version': '0.1.0',
        'docs': '/docs',
        'redoc': '/redoc',
    }
