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


def _build_initial_task_from_args(args: argparse.Namespace) -> str | None:
    """Build initial task message from --file/--task arguments.

    --file overrides --task if both are provided.
    """
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                file_content = f.read()
            return (
                f"The user has tagged a file '{args.file}'.\n"
                "Please read and understand the following file content first:\n\n"
                "```\n"
                f"{file_content}\n"
                "```\n\n"
                "After reviewing the file, please ask the user what they would like to do with it."
            )
        except Exception as e:
            # Fall back to a simple task if file cannot be read
            return f"The user attempted to share file '{args.file}', but it could not be read: {e}"
    if getattr(args, "task", None):
        return args.task
    return None


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
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Initial task for the agent to perform. Ignored if --file is provided."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a file containing the task or context. Overrides --task if both are provided."
    )

    args = parser.parse_args()

    try:
        # Build optional initial message from args
        initial_task = _build_initial_task_from_args(args)
        if initial_task is not None:
            os.environ["OPENHANDS_CLI_INITIAL_TASK"] = initial_task
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
