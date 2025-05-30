from abc import ABC, abstractmethod
from openhands.server.session.conversation_init_data import ConversationInitData


class ExperimentManager(ABC):
    @abstractmethod
    def run_conversation_variant_test(self, conversation_settings: ConversationInitData):
        ...


