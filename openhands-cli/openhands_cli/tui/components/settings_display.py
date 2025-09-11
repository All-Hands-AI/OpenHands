"""Reusable components for displaying settings in the terminal UI."""

from typing import Any, Dict, Optional
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from pydantic import SecretStr

from ...settings.constants import HIDDEN_VALUE_DISPLAY, NOT_SET_DISPLAY


class SettingsDisplay:
    """Display components for settings UI."""

    @staticmethod
    def format_value(value: Any) -> str:
        """Format a setting value for display."""
        if isinstance(value, SecretStr):
            return HIDDEN_VALUE_DISPLAY if value else NOT_SET_DISPLAY
        elif value is None:
            return NOT_SET_DISPLAY
        elif isinstance(value, bool):
            return 'Enabled' if value else 'Disabled'
        return str(value)

    @staticmethod
    def section_header(title: str, emoji: Optional[str] = None) -> None:
        """Display a section header."""
        emoji_prefix = f'{emoji} ' if emoji else ''
        print_formatted_text(HTML(f'<gold>{emoji_prefix}{title}</gold>'))
        print_formatted_text('')

    @staticmethod
    def subsection_header(title: str) -> None:
        """Display a subsection header."""
        print_formatted_text(HTML(f'<white>{title}:</white>'))

    @staticmethod
    def setting_value(label: str, value: Any, indent: int = 2) -> None:
        """Display a setting value with label."""
        indent_str = ' ' * indent
        formatted_value = SettingsDisplay.format_value(value)
        print_formatted_text(f'{indent_str}{label}: {formatted_value}')

    @staticmethod
    def settings_group(title: str, settings: Dict[str, Any], indent: int = 2) -> None:
        """Display a group of settings."""
        SettingsDisplay.subsection_header(title)
        for label, value in settings.items():
            SettingsDisplay.setting_value(label, value, indent)
        print_formatted_text('')

    @staticmethod
    def success_message(message: str) -> None:
        """Display a success message."""
        print_formatted_text(HTML(f'<green>✓ {message}</green>'))

    @staticmethod
    def warning_message(message: str) -> None:
        """Display a warning message."""
        print_formatted_text(HTML(f'<yellow>⚠ {message}</yellow>'))

    @staticmethod
    def error_message(message: str) -> None:
        """Display an error message."""
        print_formatted_text(HTML(f'<red>✗ {message}</red>'))