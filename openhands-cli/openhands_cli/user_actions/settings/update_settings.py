"""Actions for updating settings."""

from typing import Optional
from pydantic import SecretStr

from ...settings.models import CLISettings, LLMSettings, AgentSettings, OptionalSettings


class SettingsActions:
    """Actions for updating settings."""

    @staticmethod
    def update_llm_settings(
        settings: CLISettings,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> CLISettings:
        """Update LLM settings."""
        current = settings.llm
        new_settings = LLMSettings(
            model=model or current.model,
            api_key=SecretStr(api_key) if api_key is not None else current.api_key,
            base_url=base_url if base_url is not None else current.base_url
        )
        
        return CLISettings(
            llm=new_settings,
            agent=settings.agent,
            optional=settings.optional
        )

    @staticmethod
    def update_agent_settings(
        settings: CLISettings,
        agent_type: Optional[str] = None,
        confirmation_mode: Optional[bool] = None
    ) -> CLISettings:
        """Update agent settings."""
        current = settings.agent
        new_settings = AgentSettings(
            agent_type=agent_type or current.agent_type,
            confirmation_mode=(
                confirmation_mode 
                if confirmation_mode is not None 
                else current.confirmation_mode
            )
        )
        
        return CLISettings(
            llm=settings.llm,
            agent=new_settings,
            optional=settings.optional
        )

    @staticmethod
    def update_optional_settings(
        settings: CLISettings,
        search_api_key: Optional[str] = None
    ) -> CLISettings:
        """Update optional settings."""
        current = settings.optional
        new_settings = OptionalSettings(
            search_api_key=(
                SecretStr(search_api_key) 
                if search_api_key is not None 
                else current.search_api_key
            )
        )
        
        return CLISettings(
            llm=settings.llm,
            agent=settings.agent,
            optional=new_settings
        )

    @staticmethod
    def reset_to_defaults() -> CLISettings:
        """Reset all settings to defaults."""
        return CLISettings()