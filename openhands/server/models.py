from sqlalchemy import Column, DateTime, String, Table
from sqlalchemy.sql import func

from .db import metadata

# Define User table
User = Table(
    'users',
    metadata,
    Column('public_key', String, primary_key=True, nullable=False),
    # TODO: should we encrypt mnemonic?
    Column('mnemonic', String, nullable=False),
    Column('jwt', String, nullable=False),
    Column('created_at', DateTime, server_default=func.now(), nullable=False),
)
