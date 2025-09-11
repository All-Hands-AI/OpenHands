"""Interactive settings configuration UI for OpenHands CLI."""

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt

from openhands.core.config.llm_config import LLMConfig
from ..settings.manager import CLISettings
from .components.menu import SettingsMenu
from .components.settings_display import SettingsDisplay
from .components.input_handlers import InputHandler


class SettingsUI:
    """Main settings UI coordinator."""

    def __init__(self):
        """Initialize settings UI."""
        self.menu = SettingsMenu()
        self.display = SettingsDisplay()
        self.input = InputHandler()
        self.settings = CLISettings()

    def display_current_settings(self, settings: LLMConfig) -> None:
        """Display all current settings."""
        self.display.settings_group('LLM Configuration', {
            'Model': settings.model,
            'API Key': '********' if settings.api_key else None,
            'Base URL': settings.base_url,
            'Temperature': settings.temperature,
            'Top P': settings.top_p,
            'Max Output Tokens': settings.max_output_tokens
        })

    def configure_model(self, current: str) -> str:
        """Configure LLM model selection."""
        self.display.subsection_header('Select LLM Model')
        
        choices = [
            'gpt-4-turbo-preview',
            'gpt-4',
            'gpt-3.5-turbo',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'Other (specify)'
        ]
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

    def configure_api_key(self, current: str | None) -> str | None:
        """Configure LLM API key."""
        self.display.subsection_header('API Key Configuration')
        
        value, changed = self.input.get_secret_value(
            'Update API Key?',
            current=current
        )
        
        return value if changed else current

    def configure_base_url(self, current: str | None) -> str | None:
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

    def configure_temperature(self, current: float) -> float:
        """Configure temperature."""
        self.display.subsection_header('Temperature Configuration')
        
        return float(self.input.get_custom_value(
            'Enter temperature (0.0 - 1.0): ',
            current=str(current),
            validator=lambda x: 0.0 <= float(x) <= 1.0
        ))

    def configure_top_p(self, current: float) -> float:
        """Configure top p."""
        self.display.subsection_header('Top P Configuration')
        
        return float(self.input.get_custom_value(
            'Enter top p (0.0 - 1.0): ',
            current=str(current),
            validator=lambda x: 0.0 <= float(x) <= 1.0
        ))

    def configure_max_output_tokens(self, current: int | None) -> int | None:
        """Configure max output tokens."""
        self.display.subsection_header('Max Output Tokens Configuration')
        
        value = self.input.get_custom_value(
            'Enter max output tokens (leave empty for no limit): ',
            current=str(current) if current else '',
            validator=lambda x: not x or int(x) > 0
        )
        
        return int(value) if value else None

    def configure_llm_settings(self) -> None:
        """Configure LLM settings."""
        current = self.settings.llm
        
        self.display.section_header('Configure LLM Settings', '🤖')
        
        # Display current settings
        self.display_current_settings(current)
        print_formatted_text('')
        
        # Configure each setting
        model = self.configure_model(current.model)
        print_formatted_text('')
        
        api_key = self.configure_api_key(
            current.api_key.get_secret_value() if current.api_key else None
        )
        print_formatted_text('')
        
        base_url = self.configure_base_url(current.base_url)
        print_formatted_text('')
        
        temperature = self.configure_temperature(current.temperature)
        print_formatted_text('')
        
        top_p = self.configure_top_p(current.top_p)
        print_formatted_text('')
        
        max_output_tokens = self.configure_max_output_tokens(current.max_output_tokens)
        
        # Create new settings
        new_settings = LLMConfig(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_output_tokens
        )
        
        # Save settings
        self.settings.update_llm(new_settings)
        self.display.success_message('LLM settings updated successfully!')

    def reset_settings(self) -> None:
        """Reset settings to defaults."""
        if self.input.confirm_action(
            'Are you sure you want to reset all settings to defaults?'
        ):
            self.settings.reset()
            self.display.success_message('Settings reset to defaults!')

    def run(self) -> None:
        """Run the settings configuration UI."""
        while True:
            print_formatted_text('')
            
            # Display current settings
            self.menu.display_current_settings(
                lambda: self.display_current_settings(self.settings.llm)
            )
            
            # Add menu choices
            self.menu.choices.clear()
            self.menu.add_choice('Configure LLM Settings', self.configure_llm_settings)
            self.menu.add_choice('Reset to Defaults', self.reset_settings)
            
            # Run menu
            if not self.menu.run():
                break
        
        print_formatted_text('')
        self.display.warning_message('Settings configuration complete.')