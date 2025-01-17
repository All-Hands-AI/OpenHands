from __future__ import annotations

import json
from dataclasses import dataclass

from openhands.core.config.app_config import AppConfig
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.utils import load_app_config
from openhands.server.settings import Settings
from openhands.storage import get_file_store
from openhands.storage.files import FileStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.async_utils import call_sync_from_async


@dataclass
class FileSettingsStore(SettingsStore):
    file_store: FileStore
    path: str = 'settings.json'

    async def load(self) -> Settings | None:
        try:
            json_str = await call_sync_from_async(self.file_store.read, self.path)
            kwargs = json.loads(json_str)
            settings = Settings(**kwargs)
            return settings
        except FileNotFoundError:
            return await self.create_default_settings()

    async def store(self, settings: Settings):
        json_str = json.dumps(settings.__dict__)
        await call_sync_from_async(self.file_store.write, self.path, json_str)

    async def create_default_settings(self) -> Settings | None:
        """Create a set of default settings. Classes which override this may provide reasonable defaults, and even persist settings"""
        app_config = load_app_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            # If no api key has been set, we take this to mean that there is no reasonable default
            return None
        security = app_config.security
        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
        )
        return settings

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> FileSettingsStore:
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileSettingsStore(file_store)
