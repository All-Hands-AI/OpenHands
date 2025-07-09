import os

from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.utils.import_utils import get_impl


class ExperimentManager:
    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
        return conversation_settings


# Default to the new AgentExperimentManager unless overridden by environment variable
experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.agent_experiment_manager.AgentExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
