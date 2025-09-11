"""Input handling components for settings UI."""

from typing import Any, List, Optional, Tuple, Union
from prompt_toolkit.shortcuts import prompt
from pydantic import SecretStr

from ...user_actions.utils import cli_confirm


class InputHandler:
    """Input handling utilities for settings UI."""

    @staticmethod
    def get_choice(
        prompt_text: str,
        choices: List[str],
        current: Optional[Any] = None,
        escapable: bool = True
    ) -> int:
        """Get user choice from a list of options."""
        current_idx = 0
        if current is not None:
            try:
                current_idx = choices.index(str(current))
            except ValueError:
                current_idx = len(choices) - 1 if 'Other' in choices else 0

        return cli_confirm(
            prompt_text,
            choices=choices,
            initial_selection=current_idx,
            escapable=escapable
        )

    @staticmethod
    def get_custom_value(
        prompt_text: str,
        current: Optional[str] = None
    ) -> Optional[str]:
        """Get custom value input from user."""
        value = prompt(prompt_text).strip()
        return value if value else current

    @staticmethod
    def get_secret_value(
        prompt_text: str,
        current: Optional[SecretStr] = None,
        allow_clear: bool = True
    ) -> Tuple[Optional[str], bool]:
        """Get secret value input from user."""
        choices = ['Keep current', 'Enter new value']
        if allow_clear:
            choices.append('Clear value')

        action = cli_confirm(
            prompt_text,
            choices=choices,
            initial_selection=0,
            escapable=True
        )

        if action == 1:  # Enter new value
            value = prompt('Enter value (hidden): ', is_password=True).strip()
            return value if value else None, True
        elif action == 2 and allow_clear:  # Clear value
            return None, True
        else:  # Keep current
            return current.get_secret_value() if current else None, False

    @staticmethod
    def get_boolean_choice(
        prompt_text: str,
        current: bool = False
    ) -> bool:
        """Get boolean choice from user."""
        choices = ['Disabled', 'Enabled']
        current_idx = 1 if current else 0

        choice = cli_confirm(
            prompt_text,
            choices=choices,
            initial_selection=current_idx,
            escapable=True
        )

        return choice == 1  # 1 = Enabled, 0 = Disabled

    @staticmethod
    def confirm_action(
        prompt_text: str,
        default: bool = False
    ) -> bool:
        """Get confirmation for an action."""
        choices = ['No', 'Yes']
        current_idx = 1 if default else 0

        choice = cli_confirm(
            prompt_text,
            choices=choices,
            initial_selection=current_idx,
            escapable=True
        )

        return choice == 1  # 1 = Yes, 0 = No