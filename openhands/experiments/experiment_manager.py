import os

from openhands.core.config.agent_config import AgentConfig
from openhands.utils.import_utils import get_impl


class ExperimentManager:
    @staticmethod
    def run_conversation_variant_test(
        user_id, conversation_id, conversation_settings
    ):
        return conversation_settings

    @staticmethod
    def run_agent_config_variant_test(
        user_id, conversation_id, agent_config
    ):
        modified_config = agent_config.model_copy()
        custom_system_prompt = os.environ.get('OPENHANDS_SYSTEM_PROMPT_FILENAME')
        if custom_system_prompt:
            modified_config.system_prompt_filename = custom_system_prompt
        return modified_config


experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
