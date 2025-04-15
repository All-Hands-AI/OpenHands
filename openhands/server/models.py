import uuid
from sqlalchemy import UUID, Boolean, Column, DateTime, Integer, PrimaryKeyConstraint, String, Table
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

Conversation = Table(
    'conversations',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),  # Thay đổi String thành Integer và thêm autoincrement
    Column('user_id', String, nullable=False),
    Column('conversation_id', String, nullable=False),
    Column('published', Boolean, nullable=False),
)
