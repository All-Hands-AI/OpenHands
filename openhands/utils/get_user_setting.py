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
            
    return settings
