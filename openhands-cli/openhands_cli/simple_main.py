#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import traceback

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML


def main() -> None:
    """Main entry point for the OpenHands CLI.

    Raises:
        ImportError: If agent chat dependencies are missing
        Exception: On other error conditions
    """
    try:
        # Check if settings exist
        from openhands_cli.settings import CLISettings
        from openhands_cli.tui.settings_ui import SettingsUI

        settings = CLISettings()
        if not settings.has_api_key():
            # First time setup
            ui = SettingsUI()
            ui.run(first_time=True)

        # Start agent chat
        from openhands_cli.agent_chat import run_cli_entry
        run_cli_entry()

    except ImportError as e:
        print_formatted_text(
            HTML(f'<red>Error: Agent chat requires additional dependencies: {e}</red>')
        )
        print_formatted_text(
            HTML('<yellow>Please ensure the agent SDK is properly installed.</yellow>')
        )
        raise
    except KeyboardInterrupt:
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
    except EOFError:
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
    except Exception as e:
        print_formatted_text(HTML(f'<red>Error starting agent chat: {e}</red>'))
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
