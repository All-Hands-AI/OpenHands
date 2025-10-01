#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import argparse
import logging
import os

debug_env = os.getenv('DEBUG', 'false').lower()
if debug_env != '1' and debug_env != 'true':
    logging.disable(logging.WARNING)

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from openhands_cli.agent_chat import run_cli_entry


def main() -> None:
    """Main entry point for the OpenHands CLI.

    Raises:
        ImportError: If agent chat dependencies are missing
        Exception: On other error conditions
    """
    parser = argparse.ArgumentParser(
        description="OpenHands CLI - Terminal User Interface for OpenHands AI Agent"
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Conversation ID to use for the session. If not provided, a random UUID will be generated."
    )

    args = parser.parse_args()

    try:
        # Start agent chat
        run_cli_entry(resume_conversation_id=args.resume)

    except ImportError as e:
        print_formatted_text(
            HTML(f"<red>Error: Agent chat requires additional dependencies: {e}</red>")
        )
        print_formatted_text(
            HTML("<yellow>Please ensure the agent SDK is properly installed.</yellow>")
        )
        raise
    except KeyboardInterrupt:
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
    except EOFError:
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
    except Exception as e:
        print_formatted_text(HTML(f"<red>Error starting agent chat: {e}</red>"))
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
