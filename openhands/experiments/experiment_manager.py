import os

from openhands.core.config.agent_config import AgentConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.utils.import_utils import get_impl


class ExperimentManager:
    @staticmethod
    def run_conversation_variant_test(
        user_id: str, conversation_id: str, conversation_settings: ConversationInitData
    ) -> ConversationInitData:
        return conversation_settings

    @staticmethod
    def run_agent_config_variant_test(
        user_id: str, conversation_id: str, agent_config: AgentConfig
    ) -> AgentConfig:
        logger.info(
            f'Running agent config variant test for user_id={user_id}, conversation_id={conversation_id}'
        )
        return agent_config


experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
