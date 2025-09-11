"""Menu management components for settings UI."""

from typing import Callable, Dict, List, Optional
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from .input_handlers import InputHandler
from .settings_display import SettingsDisplay


class Menu:
    """Menu management for settings UI."""

    def __init__(self, title: str, emoji: Optional[str] = None):
        """Initialize menu with title and optional emoji."""
        self.title = title
        self.emoji = emoji
        self.choices: Dict[str, Callable] = {}
        self.display = SettingsDisplay()
        self.input = InputHandler()

    def add_choice(self, label: str, handler: Callable) -> None:
        """Add a menu choice with its handler function."""
        self.choices[label] = handler

    def display_menu(self) -> None:
        """Display the menu header."""
        self.display.section_header(self.title, self.emoji)

    def run(self, escapable: bool = True) -> bool:
        """Run the menu and handle user choice.
        
        Returns:
            bool: True if menu should continue, False if it should exit
        """
        self.display_menu()

        choice_labels = list(self.choices.keys()) + ['Exit']
        
        try:
            selected_idx = self.input.get_choice(
                'Select an option:',
                choices=choice_labels,
                escapable=escapable
            )

            if selected_idx == len(choice_labels) - 1:  # Exit selected
                return False

            # Execute the selected handler
            selected_label = choice_labels[selected_idx]
            handler = self.choices[selected_label]
            handler()
            
            return True

        except KeyboardInterrupt:
            # User pressed Ctrl+C or Escape
            return False


class SettingsMenu(Menu):
    """Specialized menu for settings configuration."""

    def __init__(self):
        """Initialize settings menu."""
        super().__init__('OpenHands CLI Settings', '⚙️')

    def display_current_settings(self, settings_display: Callable) -> None:
        """Display current settings before showing menu options."""
        print_formatted_text('')
        settings_display()
        print_formatted_text('')