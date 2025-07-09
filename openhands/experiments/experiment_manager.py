import os

from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.core.config.agent_config import AgentConfig
from openhands.utils.import_utils import get_impl   


class ExperimentManager:
    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
        """
        Apply experiment variations to the conversation settings.

        Args:
            user_id: The user ID
            conversation_id: The conversation ID
            conversation_settings: The original conversation settings

        Returns:
            Modified conversation settings with experiment variations applied
        """
        return conversation_settings

    @staticmethod
    def run_agent_config_variant_test(
        user_id: str, conversation_id: str, agent_config: AgentConfig
    ) -> AgentConfig:
        return agent_config


experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
