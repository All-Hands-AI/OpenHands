#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import sys

from openhands.sdk import (
    Message,
    TextContent,
)
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands_cli.tui.settings.mcp_screen import MCPScreen
from openhands_cli.user_actions.utils import get_session_prompter
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import setup_conversation, MissingAgentSpec
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.tui.tui import (
    display_help,
    display_welcome,
)
from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation
from openhands_cli.conversation_manager import ConversationManager


def _restore_tty() -> None:
    """
    Ensure terminal modes are reset in case prompt_toolkit cleanup didn't run.
    - Turn off application cursor keys (DECCKM): ESC[?1l
    - Turn off bracketed paste: ESC[?2004l
    """
    try:
        sys.stdout.write("\x1b[?1l\x1b[?2004l")
        sys.stdout.flush()
    except Exception:
        pass

def _print_exit_hint(conversation_id: str) -> None:
    """Print a resume hint with the current conversation ID."""
    print_formatted_text(HTML(f"<grey>Conversation ID:</grey> <yellow>{conversation_id}</yellow>"))
    print_formatted_text(
        HTML(
            f"<grey>Hint:</grey> run <gold>openhands-cli --resume {conversation_id}</gold> "
            "to resume this conversation."
        )
    )

def run_cli_entry(resume_conversation_id: str | None = None) -> None:
    """Run the agent chat session using the agent SDK.


    Raises:
        AgentSetupError: If agent setup fails
        KeyboardInterrupt: If user interrupts the session
        EOFError: If EOF is encountered
    """

    conversation = None
    settings_screen = SettingsScreen()

    while not conversation:
        try:
            conversation = setup_conversation(resume_conversation_id)
        except MissingAgentSpec:
            settings_screen.handle_basic_settings(escapable=False)

    display_welcome(conversation.id, bool(resume_conversation_id))

    # Create conversation runner to handle state machine logic
    runner = ConversationRunner(conversation)
    session = get_session_prompter()
    conversation_manager = ConversationManager()

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = session.prompt(
                HTML("<gold>> </gold>"),
                multiline=False,
            )

            if not user_input.strip():
                continue

            # Handle commands
            command = user_input.strip().lower()

            message = Message(
                role="user",
                content=[TextContent(text=user_input)],
            )

            if command == "/exit":
                exit_confirmation = exit_session_confirmation()
                if exit_confirmation == UserConfirmation.ACCEPT:
                    print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                    _print_exit_hint(conversation.id)
                    break

            elif command == "/settings":
                settings_screen = SettingsScreen(conversation)
                settings_screen.display_settings()
                continue

            elif command == "/mcp":
                mcp_screen = MCPScreen()
                mcp_screen.display_mcp_info(conversation.agent)
                continue

            elif command == "/clear":
                display_welcome(conversation.id)
                continue

            elif command == "/help":
                display_help()
                continue

            elif command == "/status":
                print_formatted_text(HTML(f"<grey>Conversation ID: {conversation.id}</grey>"))
                print_formatted_text(HTML("<grey>Status: Active</grey>"))
                confirmation_status = (
                    "enabled" if conversation.state.confirmation_mode else "disabled"
                )
                print_formatted_text(
                    HTML(f"<grey>Confirmation mode: {confirmation_status}</grey>")
                )
                continue

            elif command == "/confirm":
                runner.toggle_confirmation_mode()
                new_status = "enabled" if runner.is_confirmation_mode_enabled else "disabled"
                print_formatted_text(
                    HTML(f"<yellow>Confirmation mode {new_status}</yellow>")
                )
                continue

            elif command == "/resume":
                if not (
                    conversation.state.agent_status == AgentExecutionStatus.PAUSED
                    or conversation.state.agent_status
                    == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
                ):
                    print_formatted_text(
                        HTML("<red>No paused conversation to resume...</red>")
                    )
                    continue

                # Resume without new message
                message = None

            elif command == "/list":
                conversation_manager.list_conversations()
                continue

            elif command.startswith("/load "):
                conversation_id = command[6:].strip()  # Remove "/load "
                if not conversation_id:
                    print_formatted_text(HTML("<red>Please specify a conversation ID.</red>"))
                    print_formatted_text(HTML("<grey>Usage: /load <conversation_id></grey>"))
                    continue
                
                # Attempt to load the conversation
                loaded_conversation = conversation_manager.load_conversation(conversation_id)
                if loaded_conversation:
                    # If we successfully loaded a conversation, we would switch to it here
                    # For now, this is a placeholder for future enhancement
                    pass
                continue

            elif command.startswith("/view "):
                # Parse /view command with optional parameters
                args = command[6:].strip()  # Remove "/view "
                if not args:
                    print_formatted_text(HTML("<red>Please specify a conversation ID.</red>"))
                    print_formatted_text(HTML("<grey>Usage: /view <conversation_id> [--filter <type>] [--limit <num>] [--offset <num>]</grey>"))
                    print_formatted_text(HTML("<grey>Available filters: action, observation, user, agent, command, file, browse, message, think</grey>"))
                    continue
                
                # Parse arguments
                parts = args.split()
                conversation_id = parts[0]
                event_filter = None
                limit = 50
                offset = 0
                
                # Parse optional parameters
                i = 1
                while i < len(parts):
                    if parts[i] == "--filter" and i + 1 < len(parts):
                        event_filter = parts[i + 1]
                        i += 2
                    elif parts[i] == "--limit" and i + 1 < len(parts):
                        try:
                            limit = int(parts[i + 1])
                        except ValueError:
                            print_formatted_text(HTML("<red>Invalid limit value. Using default (50).</red>"))
                        i += 2
                    elif parts[i] == "--offset" and i + 1 < len(parts):
                        try:
                            offset = int(parts[i + 1])
                        except ValueError:
                            print_formatted_text(HTML("<red>Invalid offset value. Using default (0).</red>"))
                        i += 2
                    else:
                        i += 1
                
                # View the conversation
                conversation_manager.view_conversation(conversation_id, event_filter, limit, offset)
                continue

            runner.process_message(message)

            print()  # Add spacing

        except KeyboardInterrupt:
            exit_confirmation = exit_session_confirmation()
            if exit_confirmation == UserConfirmation.ACCEPT:
                print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                _print_exit_hint(conversation.id)
                break


    # Clean up terminal state
    _restore_tty()

