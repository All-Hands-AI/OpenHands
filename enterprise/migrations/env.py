import os
from logging.config import fileConfig

from alembic import context
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine, event

from storage.base import Base

DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASS = os.getenv('DB_PASS', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'openhands')
DB_SCHEMA = os.getenv('DB_SCHEMA')
DB_AUTH_TYPE = os.getenv('DB_AUTH_TYPE', 'password')  # 'password' or 'rds-iam'
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # AWS region for RDS IAM auth

GCP_DB_INSTANCE = os.getenv('GCP_DB_INSTANCE')
GCP_PROJECT = os.getenv('GCP_PROJECT')
GCP_REGION = os.getenv('GCP_REGION')

POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '25'))
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '10'))

target_metadata = Base.metadata
# Set schema for target metadata if DB_SCHEMA is provided
if DB_SCHEMA:
    target_metadata.schema = DB_SCHEMA

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


def get_engine(database_name=DB_NAME):
    """Create SQLAlchemy engine with optional database name."""
    if GCP_DB_INSTANCE:

        def get_db_connection():
            connector = Connector()
            instance_string = f'{GCP_PROJECT}:{GCP_REGION}:{GCP_DB_INSTANCE}'
            connect_kwargs = {
                'user': DB_USER,
                'password': DB_PASS.strip(),
                'db': database_name,
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
            url_params = ['ssl=require']
            if DB_SCHEMA:
                url_params.append(f'options=-csearch_path={DB_SCHEMA}')
            params_str = '&'.join(url_params)
            base_url = (
                f'postgresql+pg8000://{DB_USER}:dummy-password'
                f'@{DB_HOST}:{DB_PORT}/{database_name}'
                f'?{params_str}'
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
            url = (
                f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{database_name}'
            )
            if DB_SCHEMA:
                url += f'?options=-csearch_path={DB_SCHEMA}'
            return create_engine(
                url,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_pre_ping=True,
            )


engine = get_engine()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        version_table_schema=target_metadata.schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=target_metadata.schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
