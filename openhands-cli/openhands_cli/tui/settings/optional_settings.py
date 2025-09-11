"""Optional settings configuration UI."""

from typing import Optional

from ...settings.models import OptionalSettings
from ..components.settings_display import SettingsDisplay
from ..components.input_handlers import InputHandler


class OptionalSettingsHandler:
    """Handler for optional settings configuration."""

    def __init__(self):
        """Initialize optional settings handler."""
        self.display = SettingsDisplay()
        self.input = InputHandler()

    def display_current_settings(self, settings: OptionalSettings) -> None:
        """Display current optional settings."""
        self.display.settings_group('Optional Features', {
            'Search API Key': settings.search_api_key
        })

    def configure_search_api_key(self, current: Optional[str]) -> Optional[str]:
        """Configure search API key."""
        self.display.subsection_header('Search API Key Configuration')
        
        value, changed = self.input.get_secret_value(
            'Update Search API Key?',
            current=current,
            allow_clear=True
        )
        
        return value if changed else current

    def configure(self, current_settings: OptionalSettings) -> OptionalSettings:
        """Configure all optional settings."""
        self.display.section_header('Configure Optional Settings', '⚙️')
        
        # Display current settings
        self.display_current_settings(current_settings)
        print_formatted_text('')
        
        # Configure search API key
        search_api_key = self.configure_search_api_key(
            current_settings.search_api_key
        )
        
        # Create new settings
        new_settings = OptionalSettings(
            search_api_key=search_api_key
        )
        
        self.display.success_message('Optional settings updated successfully!')
        return new_settings