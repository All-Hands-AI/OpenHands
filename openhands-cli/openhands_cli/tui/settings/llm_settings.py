"""LLM settings configuration UI."""

from typing import Optional

from ...settings.constants import SUPPORTED_MODELS
from ...settings.models import LLMSettings
from ..components.settings_display import SettingsDisplay
from ..components.input_handlers import InputHandler


class LLMSettingsHandler:
    """Handler for LLM settings configuration."""

    def __init__(self):
        """Initialize LLM settings handler."""
        self.display = SettingsDisplay()
        self.input = InputHandler()

    def display_current_settings(self, settings: LLMSettings) -> None:
        """Display current LLM settings."""
        self.display.settings_group('LLM Configuration', {
            'Model': settings.model,
            'API Key': settings.api_key,
            'Base URL': settings.base_url
        })

    def configure_model(self, current: str) -> str:
        """Configure LLM model selection."""
        self.display.subsection_header('Select LLM Model')
        
        choices = SUPPORTED_MODELS + ['Other (specify)']
        selected_idx = self.input.get_choice(
            'Choose a model:',
            choices=choices,
            current=current
        )
        
        if selected_idx == len(choices) - 1:  # "Other" selected
            return self.input.get_custom_value(
                'Enter custom model name: ',
                current=current
            ) or current
        
        return choices[selected_idx]

    def configure_api_key(self, current: Optional[str]) -> Optional[str]:
        """Configure LLM API key."""
        self.display.subsection_header('API Key Configuration')
        
        value, changed = self.input.get_secret_value(
            'Update API Key?',
            current=current
        )
        
        return value if changed else current

    def configure_base_url(self, current: Optional[str]) -> Optional[str]:
        """Configure LLM base URL."""
        self.display.subsection_header('Base URL Configuration')
        
        choices = ['Keep current', 'Enter new URL', 'Clear URL']
        action = self.input.get_choice(
            'Update Base URL?',
            choices=choices
        )
        
        if action == 1:  # Enter new URL
            return self.input.get_custom_value(
                'Enter Base URL: ',
                current=current
            )
        elif action == 2:  # Clear URL
            return None
        
        return current

    def configure(self, current_settings: LLMSettings) -> LLMSettings:
        """Configure all LLM settings."""
        self.display.section_header('Configure LLM Settings', '🤖')
        
        # Display current settings
        self.display_current_settings(current_settings)
        print_formatted_text('')
        
        # Configure each setting
        model = self.configure_model(current_settings.model)
        print_formatted_text('')
        
        api_key = self.configure_api_key(current_settings.api_key)
        print_formatted_text('')
        
        base_url = self.configure_base_url(current_settings.base_url)
        
        # Create new settings
        new_settings = LLMSettings(
            model=model,
            api_key=api_key,
            base_url=base_url
        )
        
        self.display.success_message('LLM settings updated successfully!')
        return new_settings