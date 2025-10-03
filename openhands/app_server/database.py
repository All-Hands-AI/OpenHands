"""Database configuration and session management for OpenHands Server."""

import asyncio
import logging
from typing import AsyncGenerator

from fastapi import Request
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.util import await_only
from sqlmodel import SQLModel

from openhands.app_server.config import get_global_config

_logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def async_creator():
    config = get_global_config()
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        password = config.database.password
        conn = await connector.connect_async(
            f'{config.gcp.project}:{config.gcp.region}:{config.database.gcp_db_instance}',
            'asyncpg',
            user=config.database.user,
            password=password.get_secret_value() if password else None,
            db=config.database.name,
        )
        return conn


def _create_async_db_engine():
    config = get_global_config()
    database = config.database
    if database.gcp_db_instance:  # GCP environments

        def get_db_connection():
            connector = Connector()
            gcp = config.gcp
            instance_string = f'{gcp.project}:{gcp.region}:{database.gcp_db_instance}'
            password = database.password
            return connector.connect(
                instance_string,
                'pg8000',
                user=database.user,
                password=password.get_secret_value() if password else None,
                db=database.name,
            )

        engine = create_engine(
            'postgresql+pg8000://',
            creator=get_db_connection,
            pool_size=database.pool_size,
            max_overflow=database.max_overflow,
            pool_pre_ping=True,
        )

        def adapted_creator():
            dbapi = engine.dialect.dbapi
            from sqlalchemy.dialects.postgresql.asyncpg import (
                AsyncAdapt_asyncpg_connection,
            )

            return AsyncAdapt_asyncpg_connection(
                dbapi,
                await_only(async_creator()),
                prepared_statement_cache_size=100,
            )

        # create async connection pool with wrapped creator
        return create_async_engine(
            'postgresql+asyncpg://',
            creator=adapted_creator,
            pool_size=database.pool_size,
            max_overflow=database.max_overflow,
            pool_pre_ping=True,
        )
    else:
        return create_async_engine(
            database.url.get_secret_value(),
            pool_size=database.pool_size,
            max_overflow=database.max_overflow,
            pool_pre_ping=True,
        )


# Lazy initialization of engine and session maker
_engine = None
_async_session_local = None


def get_engine():
    """Get the database engine, creating it if necessary."""
    global _engine
    if _engine is None:
        _engine = _create_async_db_engine()
    return _engine


def get_async_session_local():
    """Get the async session maker, creating it if necessary."""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_local


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function that yields database sessions.

    This function creates a new database session for each request
    and ensures it's properly closed after use.

    Yields:
        AsyncSession: An async SQL session
    """
    async with get_async_session_local()() as session:
        try:
            yield session
        finally:
            await session.close()


async def managed_session_dependency(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency function that manages database sessions through request state.

    This function stores the database session in the request state to enable
    session reuse across multiple dependencies within the same request.
    If a session already exists in the request state, it returns that session.
    Otherwise, it creates a new session and stores it in the request state.

    Args:
        request: The FastAPI request object

    Yields:
        AsyncSession: An async SQL session stored in request state
    """
    # Check if a session already exists in the request state
    if hasattr(request.state, 'db_session'):
        # Yield the existing session
        yield request.state.db_session
    else:
        # Create a new session and store it in request state
        async with get_async_session_local()() as session:
            try:
                request.state.db_session = session
                yield session
                await session.commit()
            except Exception:
                _logger.exception('Rolling back SQL due to error', stack_info=True)
                await session.rollback()
                raise
            finally:
                # Clean up the session from request state
                if hasattr(request.state, 'db_session'):
                    delattr(request.state, 'db_session')
                await session.close()


async def unmanaged_session_dependency(request: Request) -> AsyncSession:
    """Using this dependency before others means that the database session used in
    the request must be committed / closed manually. This is useful in cases where processing
    continues after the response is sent."""
    if hasattr(request.state, 'db_session'):
        # Return the existing session
        return request.state.db_session
    else:
        # Create a new session and store it in request state
        session = get_async_session_local()()
        request.state.db_session = session
        return session


# TODO: We should delete the two methods below once we have alembic migrations set up


async def create_tables() -> None:
    """Create all database tables."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def drop_tables() -> None:
    """Drop all database tables."""
    async with get_engine().begin() as conn:
        # TODO: Really don't let this get into SAAS!
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.drop_all)
