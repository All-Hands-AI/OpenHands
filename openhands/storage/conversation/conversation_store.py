from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.app_config import AppConfig
from openhands.storage.data_models.conversation_metadata import ConversationMetadata
from openhands.storage.data_models.conversation_metadata_result_set import (
    ConversationMetadataResultSet,
)


class ConversationStore(ABC):
    """
    Storage for conversation metadata. May or may not support multiple users depending on the environment
    """

    @abstractmethod
    async def save_metadata(self, metadata: ConversationMetadata) -> None:
        """Store conversation metadata"""

    @abstractmethod
    async def get_metadata(self, conversation_id: str) -> ConversationMetadata:
        """Load conversation metadata"""

    @abstractmethod
    async def delete_metadata(self, conversation_id: str) -> None:
        """delete conversation metadata"""

    @abstractmethod
    async def exists(self, conversation_id: str) -> bool:
        """Check if conversation exists"""

    @abstractmethod
    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
    ) -> ConversationMetadataResultSet:
        """Search conversations"""

    @classmethod
    @abstractmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> ConversationStore:
        """Get a store for the user represented by the token given"""
