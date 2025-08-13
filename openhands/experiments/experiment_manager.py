import json
import os

from pydantic import BaseModel

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger
from openhands.server.session.conversation_init_data import ConversationInitData
from openhands.server.shared import file_store
from openhands.storage.locations import get_experiment_config_filename
from openhands.utils.import_utils import get_impl


class ExperimentConfig(BaseModel):
    config: dict[str, str] | None = None


def load_experiment_config(conversation_id: str) -> ExperimentConfig | None:
    try:
        file_path = get_experiment_config_filename(conversation_id)
        exp_config = file_store.read(file_path)
        return ExperimentConfig.model_validate_json(exp_config)
    except Exception as e:
        logger.warning(f'Failed to load experiment config: {e}')

    return None


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
        exp_config = load_experiment_config(conversation_id)
        logger.info(f'Got experiment config: {exp_config}')
        if exp_config:
            agent_cfg = config.get_agent_config(config.default_agent)
            try:
                for attr, value in exp_config.model_dump(exclude_unset=True).items():
                    logger.info(f'checking attrib: {attr}')
                    if hasattr(agent_cfg, attr):
                        logger.info(f'setting attrib: {attr}')
                        setattr(agent_cfg, attr, value)
            except json.JSONDecodeError:
                logger.warning('Invalid JSON in EXPERIMENT_MANAGER_DEFAULT_CONFIG')

            except Exception as e:
                logger.warning(f'Error processing exp config: {e}')
        return config


experiment_manager_cls = os.environ.get(
    'OPENHANDS_EXPERIMENT_MANAGER_CLS',
    'openhands.experiments.experiment_manager.ExperimentManager',
)
ExperimentManagerImpl = get_impl(ExperimentManager, experiment_manager_cls)
