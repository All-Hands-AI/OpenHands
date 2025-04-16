import uuid
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Table, Enum, ForeignKey, JSON
from sqlalchemy.sql import func

from .db import metadata

# Define User table
# User = Table(
#     'users',
#     metadata,
#     Column('public_key', String, primary_key=True, nullable=False),
#     # TODO: should we encrypt mnemonic?
#     Column('mnemonic', String, nullable=False),
#     Column('jwt', String, nullable=False),
#     Column('created_at', DateTime, server_default=func.now(), nullable=False),
#     Column('status', Enum('activated', 'non_activated', 'banned', name='user_status'), server_default='non_activated', nullable=False),
# )

# Define InvitationCode table
# InvitationCode = Table(
#     'invitation_codes',
#     metadata,
#     Column('code', String, primary_key=True, nullable=False),
#     Column('created_by', String, ForeignKey('users.public_key'), nullable=False),
#     Column('created_at', DateTime, server_default=func.now(), nullable=False),
#     Column('used_by', String, ForeignKey('users.public_key'), nullable=True),
#     Column('used_at', DateTime, nullable=True),
# )

Conversation = Table(
    'conversations',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),  # Thay đổi String thành Integer và thêm autoincrement
    Column('user_id', String, nullable=False),
    Column('conversation_id', String, nullable=False),
    Column('published', Boolean, nullable=False),
    Column('configs', JSON, nullable=False),
)
