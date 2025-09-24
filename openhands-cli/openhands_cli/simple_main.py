#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.formatted_text import HTML


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
        
        print_formatted_text(HTML("<b>OpenHands CLI</b>"))
        print_formatted_text(HTML(""))
        print_formatted_text(HTML("A command-line interface for OpenHands AI agent."))
        print_formatted_text(HTML(""))
        print_formatted_text(HTML("<b>Usage:</b>"))
        print_formatted_text(HTML("  openhands-cli                 Start interactive chat"))
        print_formatted_text(HTML("  openhands-cli --help          Show this help"))
        print_formatted_text(HTML(""))
        print_formatted_text(HTML("<b>Interactive Commands:</b>"))
        print_formatted_text(HTML("  /help                         Show available commands"))
        print_formatted_text(HTML("  /settings                     Open settings"))
        print_formatted_text(HTML("  /exit                         Exit the application"))
        print_formatted_text(HTML("  /clear                        Clear the screen"))
        print_formatted_text(HTML("  /status                       Show session status"))
        print_formatted_text(HTML("  /confirm                      Toggle confirmation mode"))
        print_formatted_text(HTML("  /new                          Start new conversation"))
        print_formatted_text(HTML("  /resume                       Resume paused conversation"))
        print_formatted_text(HTML(""))
        print_formatted_text(HTML("<b>Keyboard Shortcuts:</b>"))
        print_formatted_text(HTML("  Ctrl+C                        Exit (with confirmation)"))
        print_formatted_text(HTML("  Ctrl+P                        Pause agent execution"))
        return

    try:
        # Import agent chat only when actually needed
        from openhands_cli.agent_chat import run_cli_entry
        
        # Start agent chat directly by default
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
        _fast_exit()
    except EOFError:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        
        print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
        _fast_exit()
    except Exception as e:
        from prompt_toolkit import print_formatted_text
        from prompt_toolkit.formatted_text import HTML
        
        print_formatted_text(HTML(f"<red>Error starting agent chat: {e}</red>"))
        import traceback
        traceback.print_exc()
        raise


def _fast_exit():
    """Perform fast exit to avoid waiting for thread cleanup."""
    import os
    import threading
    
    # Give threads a brief moment to clean up
    active_threads = [t for t in threading.enumerate() if t != threading.current_thread()]
    if active_threads:
        # Wait briefly for daemon threads to finish
        import time
        time.sleep(0.01)
    
    # Force exit to avoid waiting for any remaining cleanup
    os._exit(0)


if __name__ == "__main__":
    main()
