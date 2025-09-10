"""Settings data model and management for OpenHands CLI."""

import json
import os
from typing import Optional

from pydantic import BaseModel, Field, SecretStr
from openhands.sdk import LocalFileStore


class CLISettings(BaseModel):
    """Settings for OpenHands CLI."""
    
    # LLM Configuration
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")
    api_key: Optional[SecretStr] = Field(default=None, description="API key for LLM")
    base_url: Optional[str] = Field(default=None, description="Base URL for LLM API")
    
    # Agent Configuration
    agent_type: str = Field(default="CodeActAgent", description="Type of agent to use")
    confirmation_mode: bool = Field(default=False, description="Enable confirmation mode")
    
    # Optional Features
    search_api_key: Optional[SecretStr] = Field(default=None, description="Search API key")
    
    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }


class SettingsManager:
    """Manages CLI settings with persistent storage."""
    
    def __init__(self, storage_path: str = "~/.openhands"):
        """Initialize settings manager.
        
        Args:
            storage_path: Path to store settings file
        """
        self.storage_path = os.path.expanduser(storage_path)
        self.file_store = LocalFileStore(self.storage_path)
        self.settings_file = "cli_settings.json"
        self._settings: Optional[CLISettings] = None
    
    def load_settings(self) -> CLISettings:
        """Load settings from storage or create defaults."""
        if self._settings is not None:
            return self._settings
            
        try:
            settings_data = self.file_store.read(self.settings_file)
            settings_dict = json.loads(settings_data)
            
            # Handle SecretStr fields properly
            if settings_dict.get('api_key'):
                settings_dict['api_key'] = SecretStr(settings_dict['api_key'])
            if settings_dict.get('search_api_key'):
                settings_dict['search_api_key'] = SecretStr(settings_dict['search_api_key'])
                
            self._settings = CLISettings(**settings_dict)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default settings and save them
            self._settings = CLISettings()
            self.save_settings(self._settings)
            
        return self._settings
    
    def save_settings(self, settings: CLISettings) -> None:
        """Save settings to storage."""
        settings_dict = settings.model_dump()
        
        # Handle SecretStr serialization
        if settings_dict.get('api_key'):
            settings_dict['api_key'] = settings.api_key.get_secret_value()
        if settings_dict.get('search_api_key'):
            settings_dict['search_api_key'] = settings.search_api_key.get_secret_value()
            
        settings_json = json.dumps(settings_dict, indent=2)
        self.file_store.write(self.settings_file, settings_json)
        self._settings = settings
    
    def update_settings(self, **kwargs) -> CLISettings:
        """Update specific settings and save."""
        current_settings = self.load_settings()
        
        # Handle SecretStr fields
        if 'api_key' in kwargs and kwargs['api_key']:
            kwargs['api_key'] = SecretStr(kwargs['api_key'])
        if 'search_api_key' in kwargs and kwargs['search_api_key']:
            kwargs['search_api_key'] = SecretStr(kwargs['search_api_key'])
            
        updated_settings = current_settings.model_copy(update=kwargs)
        self.save_settings(updated_settings)
        return updated_settings
    
    def get_effective_settings(self) -> CLISettings:
        """Get settings with environment variable overrides."""
        settings = self.load_settings()
        
        # Override with environment variables if present
        env_api_key = os.getenv('LITELLM_API_KEY') or os.getenv('OPENAI_API_KEY')
        env_model = os.getenv('LITELLM_MODEL')
        env_base_url = os.getenv('LITELLM_BASE_URL')
        
        overrides = {}
        if env_api_key:
            overrides['api_key'] = SecretStr(env_api_key)
        if env_model:
            overrides['model'] = env_model
        if env_base_url:
            overrides['base_url'] = env_base_url
            
        if overrides:
            return settings.model_copy(update=overrides)
        
        return settings