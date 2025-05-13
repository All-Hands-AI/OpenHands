

from abc import ABC, abstractmethod


class ConversationBroker(ABC):
    """
    This is an outline of how a conversation manager should work - I may need to refactor the existing class instead
    """

    @abstractmethod
    def find_conversation(self, user_id: str | None, conversation_id: str):
        """Find a conversation"""

    @abstractmethod
    def start_conversation(self, user_id: str):
        """Start a conversation"""

    @abstractmethod
    def pause_conversation(self, user_id: str | None, conversation: str):
        """Pause a conversation"""

    @abstractmethod
    def resume_conversation(self, user_id: str | None, conversation_id: str):
        """Pause a conversation"""
