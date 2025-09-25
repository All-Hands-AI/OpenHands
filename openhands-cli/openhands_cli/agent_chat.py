#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import logging
import uuid

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands_cli.tui.tui import (
    CommandCompleter,
    display_help,
    display_welcome,
)
from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation

logger = logging.getLogger(__name__)


def check_agent_config() -> bool:
    """
    Lightweight check if agent configuration exists.
    Returns True if config exists, False otherwise.
    """
    try:
        from openhands_cli.tui.settings.store import AgentStore
        agent_store = AgentStore()
        agent = agent_store.load()
        return agent is not None
    except Exception:
        return False


def run_cli_entry() -> None:
    """Run the agent chat session using the agent SDK with lazy initialization.

    Raises:
        AgentSetupError: If agent setup fails
        KeyboardInterrupt: If user interrupts the session
        EOFError: If EOF is encountered
    """

    # Fast startup - defer heavy initialization until needed
    conversation = None
    runner = None

    # Generate session ID and show welcome immediately
    session_id = str(uuid.uuid4())[:8]
    display_welcome(session_id)

    # Check if agent configuration exists and launch setup if needed
    if not check_agent_config():
        from openhands_cli.tui.settings.settings_screen import SettingsScreen
        settings_screen = SettingsScreen()
        settings_screen.handle_basic_settings(escapable=False)

    # Create prompt session with command completer
    session = PromptSession(completer=CommandCompleter())

    def ensure_agent_initialized():
        """Ensure agent and conversation are initialized."""
        nonlocal conversation, runner

        if conversation is not None:
            return  # Already initialized

        # Import heavy modules only when needed
        from openhands_cli.runner import ConversationRunner
        from openhands_cli.setup import setup_conversation

        # Initialize agent (config should already be validated by startup check)
        conversation = setup_conversation()
        runner = ConversationRunner(conversation)

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

            # Handle fast commands that don't need agent initialization
            if command == "/exit":
                exit_confirmation = exit_session_confirmation()
                if exit_confirmation == UserConfirmation.ACCEPT:
                    print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                    break

            elif command == "/clear":
                display_welcome(session_id)
                continue

            elif command == "/help":
                display_help()
                continue

            # Commands that need agent initialization
            elif command == "/settings":
                ensure_agent_initialized()
                from openhands_cli.tui.settings.settings_screen import SettingsScreen
                settings_screen_instance = SettingsScreen(conversation)
                settings_screen_instance.display_settings()
                continue

            elif command == "/status":
                print_formatted_text(HTML(f"<grey>Session ID: {session_id}</grey>"))
                if conversation is None:
                    print_formatted_text(HTML("<grey>Status: Not initialized</grey>"))
                    print_formatted_text(HTML("<grey>Agent will be initialized when you send a message</grey>"))
                else:
                    print_formatted_text(HTML("<grey>Status: Active</grey>"))
                    confirmation_status = (
                        "enabled" if conversation.state.confirmation_mode else "disabled"
                    )
                    print_formatted_text(
                        HTML(f"<grey>Confirmation mode: {confirmation_status}</grey>")
                    )
                continue

            elif command == "/confirm":
                ensure_agent_initialized()
                assert runner is not None
                runner.toggle_confirmation_mode()
                new_status = "enabled" if runner.is_confirmation_mode_enabled else "disabled"
                print_formatted_text(
                    HTML(f"<yellow>Confirmation mode {new_status}</yellow>")
                )
                continue
            elif command == "/new":
                print_formatted_text(
                    HTML("<yellow>Starting new conversation...</yellow>")
                )
                # Reset conversation and runner for new session
                conversation = None
                runner = None
                session_id = str(uuid.uuid4())[:8]
                display_welcome(session_id)
                continue

            elif command == "/resume":
                ensure_agent_initialized()
                from openhands.sdk.conversation.state import AgentExecutionStatus
                assert conversation is not None
                if not (
                    conversation.state.agent_status == AgentExecutionStatus.PAUSED
                    or conversation.state.agent_status
                    == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
                ):
                    print_formatted_text(
                        HTML("<red>No paused conversation to resume...</red>")
                    )
                    continue
            else:
                # Regular user message - ensure agent is initialized
                ensure_agent_initialized()
                assert runner is not None
                from openhands.sdk import Message, TextContent
                message = Message(
                    role="user",
                    content=[TextContent(text=user_input)],
                )
                # Process the message with the runner
                if message is not None or command == "/resume":
                    runner.process_message(message)

            print()  # Add spacing

        except KeyboardInterrupt:
            exit_confirmation = exit_session_confirmation()
            if exit_confirmation == UserConfirmation.ACCEPT:
                print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                break
