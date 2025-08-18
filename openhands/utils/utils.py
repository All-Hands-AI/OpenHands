from copy import deepcopy

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.llm.llm_registry import LLMRegistry
from openhands.server.services.conversation_stats import ConversationStats
from openhands.storage import get_file_store
from openhands.storage.data_models.settings import Settings


def setup_llm_config(config: OpenHandsConfig, settings: Settings) -> OpenHandsConfig:
    # Copying this means that when we update variables they are not applied to the shared global configuration!
    config = deepcopy(config)

    llm_config = config.get_llm_config()
    llm_config.model = settings.llm_model or ''
    llm_config.api_key = settings.llm_api_key
    llm_config.base_url = settings.llm_base_url
    config.set_llm_config(llm_config)
    return config


def create_registry_and_convo_stats(
    config: OpenHandsConfig,
    sid: str,
    user_id: str | None,
    user_settings: Settings | None = None,
) -> tuple[LLMRegistry, ConversationStats, OpenHandsConfig]:
    user_config = config
    if user_settings:
        user_config = setup_llm_config(config, user_settings)

    agent_cls = user_settings.agent if user_settings else None
    llm_registry = LLMRegistry(user_config, agent_cls)
    file_store = get_file_store(user_config.file_store, user_config.file_store_path)
    convo_stats = ConversationStats(file_store, sid, user_id)
    llm_registry.subscribe(convo_stats.register_llm)
    return llm_registry, convo_stats, user_config
