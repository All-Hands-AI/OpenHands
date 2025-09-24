#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import sys


def main() -> None:
    """Main entry point for the OpenHands CLI.

    Raises:
        ImportError: If agent chat dependencies are missing
        Exception: On other error conditions
    """
    # Handle --help early to avoid heavy imports
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h', 'help'):
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        print_formatted_text(HTML("""
<b>OpenHands CLI</b>

A command-line interface for OpenHands AI agent.

<b>Usage:</b>
  openhands-cli                 Start interactive agent chat
  openhands-cli --help          Show this help message

<b>Interactive Commands:</b>
  /help                         Show available commands
  /settings                     Configure LLM and agent settings
  /reset                        Reset conversation
  /resume                       Resume from previous conversation
  /exit                         Exit the application

<b>Examples:</b>
  openhands-cli                 # Start interactive session
  
For more information, visit: https://docs.all-hands.dev/
        """))
        return

    try:
        # Start agent chat directly by default
        from openhands_cli.agent_chat import run_cli_entry
        run_cli_entry()

    except ImportError as e:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        print_formatted_text(
            HTML(f"<red>Error: Agent chat requires additional dependencies: {e}</red>")
        )
        print_formatted_text(
            HTML("<yellow>Please ensure the agent SDK is properly installed.</yellow>")
        )
        raise
    except KeyboardInterrupt:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
    except EOFError:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
    except Exception as e:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        print_formatted_text(HTML(f"<red>Error starting agent chat: {e}</red>"))
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
