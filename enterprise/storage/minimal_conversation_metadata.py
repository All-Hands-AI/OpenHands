"""Minimal StoredConversationMetadata for enterprise tests.

This module provides a minimal StoredConversationMetadata class that avoids
the broken SDK import chain in the main codebase, allowing enterprise tests
to run successfully.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String
from storage.base import Base


class StoredConversationMetadata(Base):
    """Minimal conversation metadata model for enterprise tests."""

    __tablename__ = 'conversation_metadata'

    conversation_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accumulated_cost = Column(Float, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    llm_model = Column(String, nullable=True)
    git_provider = Column(String, nullable=True)
    trigger = Column(String, nullable=True)

    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        created_at: Optional[datetime] = None,
        last_updated_at: Optional[datetime] = None,
        accumulated_cost: Optional[float] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        llm_model: Optional[str] = None,
        git_provider: Optional[str] = None,
        trigger: Optional[str] = None,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.last_updated_at = last_updated_at or datetime.utcnow()
        self.accumulated_cost = accumulated_cost
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.llm_model = llm_model
        self.git_provider = git_provider
        self.trigger = trigger


__all__ = ['StoredConversationMetadata']
