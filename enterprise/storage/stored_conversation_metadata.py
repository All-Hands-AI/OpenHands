"""Temporary compatibility module for StoredConversationMetadata.

This module provides a minimal StoredConversationMetadata class to avoid
import issues with the main branch's broken agent_server imports.
"""

from sqlalchemy import Column, DateTime, String

from storage.base import Base


class StoredConversationMetadata(Base):
    """Minimal StoredConversationMetadata class for telemetry compatibility."""

    __tablename__ = 'telemetry_conversation_metadata'

    # Fields needed for telemetry queries
    id = Column(String, primary_key=True)
    conversation_id = Column(String)
    user_id = Column(String)
    created_at = Column(DateTime)
    llm_model = Column(String)
    git_provider = Column(String)
    trigger = Column(String)
    total_tokens = Column(String)  # Using String to match original type


__all__ = ['StoredConversationMetadata']
