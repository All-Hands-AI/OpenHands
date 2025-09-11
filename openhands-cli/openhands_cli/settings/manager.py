"""Settings manager for OpenHands CLI."""

import json
import os
from pathlib import Path
from typing import Optional

from openhands.core.config.llm_config import LLMConfig
from openhands.storage.local import LocalFileStore

from .constants import DEFAULT_MODEL


class CLISettings:
    """CLI settings manager."""

    def __init__(self):
        """Initialize settings manager."""
        self.store = LocalFileStore(os.path.expanduser('~/.openhands'))
        self.settings_file = 'settings.json'
        self._settings: Optional[dict] = None

    def _load(self) -> dict:
        """Load settings from file."""
        try:
            content = self.store.read(self.settings_file)
            return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, settings: dict) -> None:
        """Save settings to file."""
        self.store.write(self.settings_file, json.dumps(settings, indent=2))

    @property
    def settings(self) -> dict:
        """Get current settings."""
        if self._settings is None:
            self._settings = self._load()
        return self._settings

    @property
    def llm(self) -> LLMConfig:
        """Get LLM settings with defaults."""
        llm_data = self.settings.get('llm', {})
        if not llm_data:
            # Return default settings
            return LLMConfig(
                model=DEFAULT_MODEL,
                api_key=None,
                base_url=None,
                temperature=0.7,
                top_p=1.0,
                max_output_tokens=None
            )
        return LLMConfig.model_validate(llm_data)

    def update_llm(self, config: LLMConfig) -> None:
        """Update LLM settings."""
        settings = self.settings
        settings['llm'] = config.model_dump()
        self._save(settings)
        self._settings = settings

    def reset(self) -> None:
        """Reset all settings to defaults."""
        self._settings = {}
        self._save({})

    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.llm.api_key)