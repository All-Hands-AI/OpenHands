from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Table, func

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
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', String, nullable=False),
    Column('conversation_id', String, nullable=False),
    Column('published', Boolean, nullable=False),
    Column('configs', JSON, nullable=False),
    Column('title', String, nullable=False),
    Column('short_description', String, nullable=False),
    Column('status', String, nullable=False, default='available'),
    Column('created_at', DateTime, default=func.now(), nullable=False),
)

ResearchView = Table(
    'research_views',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', String, nullable=False),
    Column('ip_address', String, nullable=True),
    Column('user_agent', String, nullable=True),
    Column('created_at', DateTime, default=func.now(), nullable=False),
)

ResearchTrending = Table(
    'research_trendings',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', String, nullable=False),
    Column('total_view_24h', Integer, nullable=False),
    Column('total_view_7d', Integer, nullable=False),
    Column('total_view_30d', Integer, nullable=False),
    Column('created_at', DateTime, default=func.now(), nullable=False),
)


Mem0ConversationJob = Table(
    'mem0_conversation_jobs',
    metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('conversation_id', String, nullable=False),
    Column('events', JSON, nullable=False),
    Column('metadata', JSON, nullable=False),
    Column('status', String, nullable=False, default='pending'),
    Column('error', String, nullable=True),
    Column('created_at', DateTime, default=func.now(), nullable=False),
)
