from openhands.core.plugins.openhands_plugin import OpenHandsPlugin
from openhands.core.plugins.plugin_schema import MissingPluginException, PluginSchema
from openhands.storage.settings.settings_store import SettingsStore


class PluginRegistry:
    _instance = None
    _plugins: list[type[PluginSchema]] = []

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_plugin(self, plugin: type[PluginSchema]):
        self._plugins.append(plugin)

    async def get_settings_store(self) -> type[SettingsStore]:
        # Return the last registered implementation or default
        for plugin in reversed(self._plugins):
            store = await plugin.get_settings_store()
            return store

        raise MissingPluginException('Did not find plugin for settings store')
