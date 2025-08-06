from copy import deepcopy

from openhands.core.config.openhands_config import OpenHandsConfig
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
