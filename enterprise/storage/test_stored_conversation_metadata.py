"""Test-only StoredConversationMetadata to avoid broken import chains.

This module provides a minimal StoredConversationMetadata class for testing
that avoids the broken SDK imports in the main branch while maintaining
the same table schema for compatibility.
"""

import uuid
from sqlalchemy import Column, DateTime, Float, Integer, String
from storage.base import Base


class StoredConversationMetadata(Base):  # type: ignore
    """Test-only conversation metadata storage.
    
    This class replicates the schema from the main codebase for testing
    purposes while avoiding the broken import chain that includes SDK imports.
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
    pr_number = Column(String, nullable=True)  # Simplified for testing
    
    # Cost and token metrics
    accumulated_cost = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    max_budget_per_task = Column(Float, nullable=True)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    reasoning_tokens = Column(Integer, default=0)
    context_window = Column(Integer, default=0)
    per_turn_token = Column(Integer, default=0)
    
    # LLM model used for the conversation
    llm_model = Column(String, nullable=True)
    
    conversation_version = Column(String, nullable=False, default='V0')
    sandbox_id = Column(String, nullable=True)


__all__ = ['StoredConversationMetadata']