from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from openhands.app_server.database import create_tables


@asynccontextmanager
async def v1_lifespan(api: FastAPI) -> AsyncIterator[None]:
    # TODO: Replace this with an invocation of the alembic migrations
    await create_tables()
    yield
    # await drop_tables()
