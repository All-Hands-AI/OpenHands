from openhands.core.config.llm_config import LLMConfig
from openhands.server.settings import Settings
from openhands.server.shared import (
    SettingsStoreImpl,
    config,
)


async def get_user_setting(user_id: str | None, useDefaultSettings: bool = True):
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()

    if not settings and useDefaultSettings:
        # # If no settings found for user, load default settings
        # default_store = await SettingsStoreImpl.get_instance(config, None)
        # settings = await default_store.load()
        # if not settings:
        settings = Settings.from_config()

    # use global config instead of user settings
    if settings:
        llm_config: LLMConfig = config.get_llm_config()

        settings.enable_default_condenser = config.enable_default_condenser
        settings.llm_model = llm_config.model
        settings.llm_api_key = llm_config.api_key
        settings.llm_base_url = llm_config.base_url

    return settings
