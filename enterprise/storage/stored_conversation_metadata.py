"""Compatibility module for StoredConversationMetadata.

This module provides access to StoredConversationMetadata for the enterprise
telemetry framework. We reuse the existing table schema from the main codebase
but define it locally to avoid import dependency issues.

The table schema matches openhands.app_server.app_conversation.sql_app_conversation_info_service.StoredConversationMetadata
to maintain compatibility with existing enterprise foreign key relationships.
"""

import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String
from storage.base import Base


class StoredConversationMetadata(Base):  # type: ignore
    """Conversation metadata storage compatible with main OpenHands schema.
    
    This class replicates the schema from the main codebase to avoid import
    dependency issues while maintaining full compatibility with existing
    enterprise tables that reference this via foreign keys.
    """

    __tablename__ = 'conversation_metadata'
    
    # Core fields matching the main codebase schema
    conversation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_user_id = Column(String, nullable=True)
    user_id = Column(String, nullable=False)
    selected_repository = Column(String, nullable=True)
    selected_branch = Column(String, nullable=True)
    git_provider = Column(String, nullable=True)
    title = Column(String, nullable=True)
    last_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    trigger = Column(String, nullable=True)
    
    # Cost and token metrics
    accumulated_cost = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    max_budget_per_task = Column(Float, nullable=True)
    cache_read_tokens = Column(Integer, default=0)


__all__ = ['StoredConversationMetadata']
