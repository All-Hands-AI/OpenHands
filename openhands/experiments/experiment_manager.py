import os

from openhands.core.config.openhands_config import OpenHandsConfig
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
    def run_config_variant_test(
        user_id: str, conversation_id: str, config: OpenHandsConfig
    ) -> OpenHandsConfig:
        logger.debug(
            f'Running agent config variant test for user_id={user_id}, conversation_id={conversation_id}'
        )
        return config


experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
