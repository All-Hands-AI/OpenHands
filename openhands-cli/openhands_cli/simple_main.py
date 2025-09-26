#!/usr/bin/env python3
"""
Simple main entry point for OpenHands CLI.
This is a simplified version that demonstrates the TUI functionality.
"""

import logging
import os


from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from openhands_cli.agent_chat import run_cli_entry


def configure_logging() -> None:
    """Configure logging to silence INFO logs from upstream packages."""

    debug_env = os.getenv('DEBUG', 'false').lower()
    if debug_env == '1' or debug_env == 'true':
        return

    # Set logging level to WARNING for openhands.sdk and openhands.tools packages
    # This will silence INFO logs but keep WARNING and ERROR logs
    logging.getLogger("openhands.sdk").setLevel(logging.CRITICAL)
    logging.getLogger("openhands.tools").setLevel(logging.CRITICAL)

    # Also silence specific loggers that were observed to be noisy
    logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.CRITICAL)
    logging.getLogger("fastmcp").setLevel(logging.CRITICAL)
    
    # Silence MCP tool manager warnings about failed server connections
    logging.getLogger("fastmcp.tools.tool_manager").setLevel(logging.CRITICAL)
    
    # Try to catch the specific logger that's causing the MCP warning
    # The warning shows "tool_manager.py:86" so let's try different variations
    logging.getLogger("mcp.server.fastmcp.tools.tool_manager").setLevel(logging.CRITICAL)
    logging.getLogger("mcp").setLevel(logging.CRITICAL)


def main() -> None:
    """Main entry point for the OpenHands CLI.

    Raises:
        ImportError: If agent chat dependencies are missing
        Exception: On other error conditions
    """
    # Configure logging before any other imports or operations
    configure_logging()

    try:
        # Start agent chat directly by default
        run_cli_entry()

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
