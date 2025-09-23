import asyncio
import os
from typing import Any

from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.util import await_only

DB_HOST = os.environ.get('DB_HOST', 'localhost')  # for non-GCP environments
DB_PORT = os.environ.get('DB_PORT', '5432')  # for non-GCP environments
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres').strip()
DB_NAME = os.environ.get('DB_NAME', 'openhands')
DB_SCHEMA = os.environ.get('DB_SCHEMA')  # PostgreSQL schema name
DB_AUTH_TYPE = os.environ.get('DB_AUTH_TYPE', 'password')  # 'password' or 'rds-iam'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')  # AWS region for RDS IAM auth

GCP_DB_INSTANCE = os.environ.get('GCP_DB_INSTANCE')  # for GCP environments
GCP_PROJECT = os.environ.get('GCP_PROJECT')
GCP_REGION = os.environ.get('GCP_REGION')

POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '25'))
MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '10'))

# RDS IAM authentication setup
if DB_AUTH_TYPE == 'rds-iam':
    import boto3

    # boto3 client (reused for token generation)
    rds = boto3.client('rds', region_name=AWS_REGION)

    def get_auth_token():
        """Generate a fresh IAM DB auth token."""
        return rds.generate_db_auth_token(
            DBHostname=DB_HOST, Port=DB_PORT, DBUsername=DB_USER
        )


def _get_db_engine():
    if GCP_DB_INSTANCE:  # GCP environments

        def get_db_connection():
            connector = Connector()
            instance_string = f'{GCP_PROJECT}:{GCP_REGION}:{GCP_DB_INSTANCE}'
            connect_kwargs = {
                'user': DB_USER,
                'password': DB_PASS,
                'db': DB_NAME,
            }
            # Add schema support for GCP connections
            if DB_SCHEMA:
                connect_kwargs['options'] = f'-csearch_path={DB_SCHEMA}'
            return connector.connect(instance_string, 'pg8000', **connect_kwargs)

        return create_engine(
            'postgresql+pg8000://',
            creator=get_db_connection,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_pre_ping=True,
        )
    else:
        if DB_AUTH_TYPE == 'rds-iam':
            # Build a SQLAlchemy connection URL with a dummy password — token will be injected dynamically
            # Note: SSL is enabled by default for pg8000 when connecting to RDS, no need to specify ssl=require
            url_params = []
            if DB_SCHEMA:
                url_params.append(f'options=-csearch_path={DB_SCHEMA}')
            
            if url_params:
                params_str = '&'.join(url_params)
                base_url = (
                    f'postgresql+pg8000://{DB_USER}:dummy-password'
                    f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
                    f'?{params_str}'
                )
            else:
                base_url = (
                    f'postgresql+pg8000://{DB_USER}:dummy-password'
                    f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
                )
            engine = create_engine(
                base_url,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_pre_ping=True,
            )

            # Hook: before a connection is made, inject a fresh token
            @event.listens_for(engine, 'do_connect')
            def provide_token(dialect, conn_rec, cargs, cparams):
                token = get_auth_token()
                # Replace password in connect arguments
                cparams['password'] = token
                return dialect.connect(*cargs, **cparams)

            return engine
        else:
            host_string = (
                f'postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            )
            if DB_SCHEMA:
                host_string += f'?options=-csearch_path={DB_SCHEMA}'
            return create_engine(
                host_string,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_pre_ping=True,
            )


async def async_creator():
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        connect_kwargs: dict[str, Any] = {
            'user': DB_USER,
            'password': DB_PASS,
            'db': DB_NAME,
        }
        # Add schema support for async GCP connections
        if DB_SCHEMA:
            connect_kwargs['server_settings'] = {'search_path': DB_SCHEMA}
        conn = await connector.connect_async(
            f'{GCP_PROJECT}:{GCP_REGION}:{GCP_DB_INSTANCE}',  # Cloud SQL instance connection name"
            'asyncpg',
            **connect_kwargs,
        )
        return conn


def _get_async_db_engine():
    if GCP_DB_INSTANCE:  # GCP environments

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
            # Use NullPool to disable connection pooling and avoid event loop issues
            poolclass=NullPool,
        )
    else:
        if DB_AUTH_TYPE == 'rds-iam':
            # Build a SQLAlchemy connection URL with a dummy password — token will be injected dynamically
            # Note: SSL is enabled by default for asyncpg when connecting to RDS, no need to specify ssl=require
            url_params = []
            if DB_SCHEMA:
                url_params.append(f'options=-csearch_path={DB_SCHEMA}')
            
            if url_params:
                params_str = '&'.join(url_params)
                base_url = (
                    f'postgresql+asyncpg://{DB_USER}:dummy-password'
                    f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
                    f'?{params_str}'
                )
            else:
                base_url = (
                    f'postgresql+asyncpg://{DB_USER}:dummy-password'
                    f'@{DB_HOST}:{DB_PORT}/{DB_NAME}'
                )
            engine = create_async_engine(
                base_url, echo=True, pool_pre_ping=True, poolclass=NullPool
            )

            # Hook: before a connection is made, inject a fresh token
            @event.listens_for(engine.sync_engine, 'do_connect')
            def provide_token(dialect, conn_rec, cargs, cparams):
                token = get_auth_token()
                # Replace password in connect arguments
                cparams['password'] = token
                return dialect.connect(*cargs, **cparams)

            return engine
        else:
            host_string = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            if DB_SCHEMA:
                host_string += f'?options=-csearch_path={DB_SCHEMA}'
            return create_async_engine(
                host_string,
                # Use NullPool to disable connection pooling and avoid event loop issues
                poolclass=NullPool,
            )


engine = _get_db_engine()
session_maker = sessionmaker(bind=engine)

a_engine = _get_async_db_engine()
a_session_maker = sessionmaker(
    bind=a_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # Configure the session to use the same connection for all operations in a transaction
    # This helps prevent the "Task got Future attached to a different loop" error
    future=True,
)
