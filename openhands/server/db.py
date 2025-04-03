import os

from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')
SQLALCHEMY_DATABASE_URI = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# Create the SQLAlchemy async engine
engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    echo=True,  # Enable SQL query logging
    pool_pre_ping=True,  # Enable connection health checks
)

# Create Database instance for use with FastAPI
database = Database(SQLALCHEMY_DATABASE_URI)

# Create MetaData instance
metadata = MetaData()


async def init_db() -> None:
    """Initialize database tables."""

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
