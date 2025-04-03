from openhands.server.settings import Settings
from openhands.server.shared import (
    SettingsStoreImpl,
    config,
)


async def get_user_setting(user_id: str | None, useDefaultSettings: bool = False):
    settings_store = await SettingsStoreImpl.get_instance(config, user_id)
    settings = await settings_store.load()
    if useDefaultSettings:
        # FIXME: remove this when user want to use custom settings
        settings = Settings.from_config()

    return settings
