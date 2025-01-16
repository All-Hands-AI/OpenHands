from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.app_config import AppConfig
from openhands.server.data_models.conversation_metadata import ConversationMetadata


class ConversationStore(ABC):
    """
    Storage for conversation metadata. May or may not support multiple users depending on the environment
    """

    @abstractmethod
    async def save_metadata(self, metadata: ConversationMetadata):
        """Store conversation metadata"""

    @abstractmethod
    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        """Load conversation metadata"""

    @abstractmethod
    async def exists(self, conversation_id: str) -> bool:
        """Check if conversation exists"""

    @classmethod
    @abstractmethod
    async def get_instance(
        cls, config: AppConfig, token: str | None
    ) -> ConversationStore:
        """Get a store for the user represented by the token given"""
