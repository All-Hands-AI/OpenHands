from abc import abstractmethod
from openhands.storage.settings.settings_store import SettingsStore


class MissingPluginException(Exception):
    """Raised when no plugin was found for the plugin registry."""


class PluginSchema:
    @abstractmethod
    async def get_settings_store(self) -> type[SettingsStore]:
        """Get the settings store implementation."""
        ...
