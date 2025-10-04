"""Database configuration and session management for OpenHands Server."""

import asyncio
import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import Request
from pydantic import BaseModel, PrivateAttr, SecretStr, model_validator
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from storage.database import sessionmaker

_logger = logging.getLogger(__name__)


class DbService(BaseModel):
    persistence_dir: Path
    host: str | None = None
    port: int | None = None
    name: str | None = None
    user: str | None = None
    password: SecretStr | None = None
    echo: bool = False
    pool_size: int = 25
    max_overflow: int = 10
    gcp_db_instance: str | None = None
    gcp_project: str | None = None
    gcp_region: str | None = None

    # Private attrs
    _engine: Engine | None = PrivateAttr(default=None)
    _async_engine: AsyncEngine | None = PrivateAttr(default=None)
    _session_maker: sessionmaker | None = PrivateAttr(default=None)
    _async_session_maker: async_sessionmaker | None = PrivateAttr(default=None)

    @model_validator(mode='after')
    def fill_empty_fields(self):
        """Override any defaults with values from legacy enviroment variables"""
        if self.host is None:
            self.host = os.getenv('DB_HOST')
        if self.port is None:
            self.port = int(os.getenv('DB_PORT', '5432'))
        if self.name is None:
            self.name = os.getenv('DB_NAME', 'openhands')
        if self.user is None:
            self.user = os.getenv('DB_USER', 'postgres')
        if self.password is None:
            self.password = SecretStr(os.getenv('DB_PASS', 'postgres'))
        if self.gcp_db_instance is None:
            self.gcp_db_instance = os.getenv('GCP_DB_INSTANCE')
        if self.gcp_project is None:
            self.gcp_project = os.getenv('GCP_PROJECT')
        if self.gcp_region is None:
            self.gcp_region = os.getenv('GCP_REGION')

    def _create_gcp_db_connection(self):
        # Lazy import because lib does not import if user does not have posgres installed
        from google.cloud.sql.connector import Connector

        connector = Connector()
        instance_string = f'{self.gcp_project}:{self.gcp_region}:{self.gcp_db_instance}'
        password = self.password
        return connector.connect(
            instance_string,
            'pg8000',
            user=self.user,
            password=password.get_secret_value() if password else None,
            db=self.name,
        )

    async def _create_async_gcp_db_connection(self):
        # Lazy import because lib does not import if user does not have posgres installed
        from google.cloud.sql.connector import Connector

        loop = asyncio.get_running_loop()
        async with Connector(loop=loop) as connector:
            password = self.password
            conn = await connector.connect_async(
                f'{self.gcp_project}:{self.gcp_region}:{self.gcp_db_instance}',
                'asyncpg',
                user=self.user,
                password=password.get_secret_value() if password else None,
                db=self.name,
            )
            return conn

    def _create_gcp_engine(self):
        engine = create_engine(
            'postgresql+pg8000://',
            creator=self._create_gcp_db_connection,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
        )
        return engine

    async def _create_async_gcp_creator(self):
        from sqlalchemy.dialects.postgresql.asyncpg import (
            AsyncAdapt_asyncpg_connection,
        )

        engine = self._create_gcp_engine()

        return AsyncAdapt_asyncpg_connection(
            engine.dialect.dbapi,
            await self._create_async_gcp_db_connection(),
            prepared_statement_cache_size=100,
        )

    async def _create_async_gcp_engine(self):
        return create_async_engine(
            'postgresql+asyncpg://',
            creator=self._create_async_gcp_creator(),
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
        )

    async def get_async_db_engine(self) -> AsyncEngine:
        async_engine = self._async_engine
        if async_engine:
            return async_engine
        if self.gcp_db_instance:  # GCP environments
            async_engine = await self._create_async_gcp_engine()
        else:
            if self.host:
                url = f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'
            else:
                url = f'sqlite+aiosqlite:///{str(self.persistence_dir)}/openhands.db'

            async_engine = create_async_engine(
                url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
            )
        self._async_engine = async_engine
        return async_engine

    def get_db_engine(self) -> Engine:
        engine = self._engine
        if engine:
            return engine
        if self.gcp_db_instance:  # GCP environments
            engine = self._create_gcp_engine()
        else:
            if self.host:
                url = f'postgresql+pg8000://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}'
            else:
                url = f'sqlite:///{self.persistence_dir}/openhands.db'
            engine = create_engine(
                url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=True,
            )
        self._engine = engine
        return engine

    def get_session_maker(self) -> sessionmaker:
        session_maker = self._session_maker
        if session_maker is None:
            session_maker = sessionmaker(bind=self.get_db_engine())
            self._session_maker = session_maker
        return session_maker

    async def get_async_session_maker(self) -> async_sessionmaker:
        async_session_maker = self._async_session_maker
        if async_session_maker is None:
            db_engine = await self.get_async_db_engine()
            async_session_maker = async_sessionmaker(
                db_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            self._async_session_maker = async_session_maker
        return async_session_maker

    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Dependency function that yields database sessions.

        This function creates a new database session for each request
        and ensures it's properly closed after use.

        Yields:
            AsyncSession: An async SQL session
        """
        session_maker = await self.get_async_session_maker()
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def managed_session_dependency(
        self,
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
        db_session = getattr(request.state, 'db_session', None)
        if db_session:
            yield db_session
        else:
            # Create a new session and store it in request state
            session_maker = await self.get_async_session_maker()
            async with session_maker() as db_session:
                try:
                    setattr(request.state, 'db_session', db_session)
                    yield db_session
                    await db_session.commit()
                except Exception:
                    _logger.exception('Rolling back SQL due to error', stack_info=True)
                    await db_session.rollback()
                    raise
                finally:
                    # Clean up the session from request state
                    if hasattr(request.state, 'db_session'):
                        delattr(request.state, 'db_session')
                    await db_session.close()

    async def unmanaged_session_dependency(self, request: Request) -> AsyncSession:
        """Using this dependency before others means that the database session used in
        the request must be committed / closed manually. This is useful in cases where processing
        continues after the response is sent."""
        db_session = getattr(request.state, 'db_session', None)
        if db_session:
            return db_session
        session_maker = await self.get_async_session_maker()
        db_session = session_maker()
        setattr(request.state, 'db_session', db_session)
        return db_session
