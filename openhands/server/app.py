import logging
import warnings
from contextlib import asynccontextmanager

with warnings.catch_warnings():
    warnings.simplefilter('ignore')

from fastapi import (
    FastAPI,
)

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands import __version__
from openhands.server.backend_pre_start import init
from openhands.server.db import database, engine
from openhands.server.initial_data import init as init_initial_data
from openhands.server.routes.auth import app as auth_router
from openhands.server.routes.conversation import app as conversation_api_router
from openhands.server.routes.feedback import app as feedback_api_router
from openhands.server.routes.files import app as files_api_router
from openhands.server.routes.github import app as github_api_router
from openhands.server.routes.manage_conversations import (
    app as manage_conversation_api_router,
)
from openhands.server.routes.public import app as public_api_router
from openhands.server.routes.security import app as security_api_router
from openhands.server.routes.settings import app as settings_router
from openhands.server.routes.trajectory import app as trajectory_router
from openhands.server.shared import conversation_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    try:
        # Connect to database
        await database.connect()

        # Initialize database connection
        await init(engine)
        await init_initial_data()

        # Start conversation manager
        async with conversation_manager:
            yield
    except Exception as e:
        logger.error(f'Error during startup: {e}')
        raise
    finally:
        # Disconnect from database
        await database.disconnect()


app = FastAPI(
    title='OpenHands',
    description='OpenHands: Code Less, Make More',
    version=__version__,
    lifespan=_lifespan,
)


@app.get('/health')
async def health():
    return 'OK'


app.include_router(public_api_router)
app.include_router(files_api_router)
app.include_router(security_api_router)
app.include_router(feedback_api_router)
app.include_router(conversation_api_router)
app.include_router(manage_conversation_api_router)
app.include_router(settings_router)
app.include_router(github_api_router)
app.include_router(trajectory_router)
app.include_router(auth_router)
