from __future__ import annotations

import json
import traceback
from dataclasses import dataclass, field
from typing import Any

from pydantic import SecretStr

from openhands.core import logger
from openhands.core.config.app_config import AppConfig

from openhands.core.config.config_save import (
    _get_value_from_path, # Use helper to read from AppConfig
    save_setting_to_user_toml,
)
from openhands.server.settings import Settings
from openhands.storage import get_file_store
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore
from openhands.storage.settings.settings_store import SettingsStore
from openhands.utils.async_utils import call_sync_from_async

# Maps fields from the Settings model (used by UI/API) to AppConfig paths for user TOML saving
SETTINGS_TO_APPCONFIG_MAP = {
    'agent': 'default_agent',
    'max_iterations': 'max_iterations',
    'security_analyzer': 'security.security_analyzer',
    'confirmation_mode': 'security.confirmation_mode',
    'llm_model': 'llm.model', # Assumes default [llm] section
    'llm_base_url': 'llm.base_url', # Assumes default [llm] section
    'enable_default_condenser': 'enable_default_condenser',
    'sandbox_base_container_image': 'sandbox.base_container_image',
    'sandbox_runtime_container_image': 'sandbox.runtime_container_image',
    # Fields NOT mapped (likely UI/Server specific or need separate handling):
    # language, enable_sound_notifications, user_consents_to_analytics, remote_runtime_resource_factor
    # llm_api_key - moved to secrets store
}


@dataclass
class FileSettingsStore(SettingsStore):
    """
    Stores and retrieves settings by writing to/reading from the user's
    ~/.openhands/config.toml file.
    Requires the runtime AppConfig instance to access the TOML snapshot
    for safe saving and to reconstruct the Settings object.
    """

    app_config: AppConfig = field(init=False) # Set by get_instance

    async def load(self) -> Settings | None:
        """
        Constructs a Settings object based on the current runtime AppConfig.
        Does NOT read the user TOML file directly here, as that's part of the initial load.
        """
        logger.openhands_logger.info("Loading settings from runtime AppConfig for FileSettingsStore")
        if not hasattr(self, 'app_config'):
             logger.openhands_logger.error("AppConfig not set in FileSettingsStore instance. Cannot load settings.")
             return None

        settings_data = {}
        try:
            # Populate settings_data using the mapping
            for settings_key, appconfig_path in SETTINGS_TO_APPCONFIG_MAP.items():
                try:
                    # Use helper to safely get potentially nested values
                    settings_data[settings_key] = _get_value_from_path(self.app_config, appconfig_path)
                except (AttributeError, KeyError, TypeError, NotImplementedError):
                    logger.openhands_logger.debug(f"Path '{appconfig_path}' not found in AppConfig for setting '{settings_key}'. Skipping.")
                    settings_data[settings_key] = None # Or use Settings model default?

            # Instantiate the Settings object
            settings = Settings(**settings_data)
            return settings

        except Exception as e:
            logger.openhands_logger.error(f"Unexpected error loading settings from AppConfig: {e}\n{traceback.format_exc()}")
            return None


    async def store(self, settings: Settings) -> None:
        """
        Saves relevant fields from the Settings object to the user's config TOML file.
        Uses the save_setting_to_user_toml function which handles snapshot comparison.
        """
        logger.openhands_logger.info("Storing settings via FileSettingsStore to user TOML")
        if not hasattr(self, 'app_config'):
             logger.openhands_logger.error("AppConfig not set in FileSettingsStore instance. Cannot store settings.")
             return

        tasks = []

        # Use model_dump to iterate through fields present in the input 'settings' object
        settings_dict = settings.model_dump(exclude_none=True)

        for field_name, value in settings_dict.items():
            if field_name in SETTINGS_TO_APPCONFIG_MAP:
                setting_path = SETTINGS_TO_APPCONFIG_MAP[field_name]
                tasks.append(
                    call_sync_from_async(
                        save_setting_to_user_toml,
                        self.app_config,
                        setting_path,
                        value
                    )
                )
            else:
                 logger.openhands_logger.debug(f"No AppConfig path mapping found for setting '{field_name}'. Skipping save.")

        # Execute all save tasks (could potentially run in parallel if save_setting is thread-safe)
        # For simplicity, run sequentially for now.
        for task in tasks:
            try:
                await task
            except Exception as e:
                # Error is logged within save_setting_to_user_toml, but maybe log context here too
                logger.openhands_logger.error(f"Error occurred during async save task: {e}")


    @classmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None # user_id currently unused by FileSettingsStore
    ) -> FileSettingsStore:
        # Removed file_store dependency as we write directly via tomlkit now
        instance = cls()
        instance.app_config = config # Store the runtime config instance
        logger.openhands_logger.debug("Created FileSettingsStore instance")
        return instance
