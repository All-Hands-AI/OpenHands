from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import SecretStr

from openhands.core.config.app_config import AppConfig
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
            return None

    async def store(self, settings: Settings) -> None:
        json_str = settings.model_dump_json(context={'expose_secrets': True})
        await call_sync_from_async(self.file_store.write, self.path, json_str)

    async def reset(self) -> None:
        existing_settings = await self.load()
        if existing_settings:
            reset_settings = Settings(
                language='en',
                agent='CodeActAgent',
                max_iterations=100,
                security_analyzer='',
                confirmation_mode=False,
                llm_model='anthropic/claude-3-5-sonnet-20241022',
                llm_api_key=SecretStr(''),
                llm_base_url='',
                remote_runtime_resource_factor=1,
                github_token=existing_settings.github_token,
                user_consents_to_analytics=existing_settings.user_consents_to_analytics,
            )
            await self.store(reset_settings)

    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> FileSettingsStore:
        file_store = get_file_store(config.file_store, config.file_store_path)
        return FileSettingsStore(file_store)
