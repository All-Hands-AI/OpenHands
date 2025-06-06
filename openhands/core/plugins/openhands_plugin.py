from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.plugins.plugin_schema import PluginSchema
from openhands.storage.settings.settings_store import SettingsStore
from openhands.storage.settings.file_settings_store import FileSettingsStore


class OpenHandsPlugin(PluginSchema):
    """Base class for OpenHands plugins."""
    def __init__(self, config: OpenHandsConfig):
        self.config = config

    async def get_settings_store(self) -> type[SettingsStore]:
        """Get the settings store implementation."""
        return await FileSettingsStore.get_instance(self.config)

