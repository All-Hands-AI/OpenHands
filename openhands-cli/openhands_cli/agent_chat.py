#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import logging
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openhands.sdk import Message, TextContent
    from openhands.sdk.conversation.state import AgentExecutionStatus
    from prompt_toolkit import PromptSession, print_formatted_text
    from prompt_toolkit.formatted_text import HTML
    from openhands_cli.runner import ConversationRunner
    from openhands_cli.setup import setup_agent
    from openhands_cli.tui.settings.settings_screen import SettingsScreen
    from openhands_cli.tui.tui import CommandCompleter, display_help, display_welcome
    from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation

logger = logging.getLogger(__name__)


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


def run_cli_entry() -> None:
    """Run the agent chat session using the agent SDK.

    Raises:
        AgentSetupError: If agent setup fails
        KeyboardInterrupt: If user interrupts the session
        EOFError: If EOF is encountered
    """
    # Import heavy dependencies only when needed
    from openhands_cli.setup import setup_agent
    from openhands_cli.tui.settings.settings_screen import SettingsScreen
    from openhands_cli.tui.tui import display_welcome, CommandCompleter
    from openhands_cli.runner import ConversationRunner
    from prompt_toolkit import PromptSession

    conversation = setup_agent()
    settings_screen = SettingsScreen()

    while not conversation:
        settings_screen.handle_basic_settings(escapable=False)
        conversation = setup_agent()

    # Generate session ID
    session_id = str(uuid.uuid4())[:8]

    display_welcome(session_id)

    # Create prompt session with command completer
    session = PromptSession(completer=CommandCompleter())

    # Create conversation runner to handle state machine logic
    runner = ConversationRunner(conversation)

    # Main chat loop
    while True:
        try:
            from prompt_toolkit.formatted_text import HTML
            
            # Get user input
            user_input = session.prompt(
                HTML("<gold>> </gold>"),
                multiline=False,
            )

            if not user_input.strip():
                continue

            # Handle commands
            command = user_input.strip().lower()

            # Import SDK components only when needed
            from openhands.sdk import Message, TextContent
            
            message = Message(
                role="user",
                content=[TextContent(text=user_input)],
            )

            if command == "/exit":
                from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation
                from prompt_toolkit import print_formatted_text
                
                exit_confirmation = exit_session_confirmation()
                if exit_confirmation == UserConfirmation.ACCEPT:
                    print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                    _fast_exit()
                    break

            elif command == "/settings":
                settings_screen = SettingsScreen(conversation)
                settings_screen.display_settings()
                continue

            elif command == "/clear":
                display_welcome(session_id)
                continue
            elif command == "/help":
                from openhands_cli.tui.tui import display_help
                display_help()
                continue
            elif command == "/status":
                from prompt_toolkit import print_formatted_text
                
                print_formatted_text(HTML(f"<grey>Session ID: {session_id}</grey>"))
                print_formatted_text(HTML("<grey>Status: Active</grey>"))
                confirmation_status = (
                    "enabled" if conversation.state.confirmation_mode else "disabled"
                )
                print_formatted_text(
                    HTML(f"<grey>Confirmation mode: {confirmation_status}</grey>")
                )
                continue
            elif command == "/confirm":
                from prompt_toolkit import print_formatted_text
                
                current_mode = runner.confirmation_mode
                runner.set_confirmation_mode(not current_mode)
                new_status = "enabled" if not current_mode else "disabled"
                print_formatted_text(
                    HTML(f"<yellow>Confirmation mode {new_status}</yellow>")
                )
                continue
            elif command == "/new":
                from prompt_toolkit import print_formatted_text
                
                print_formatted_text(
                    HTML("<yellow>Starting new conversation...</yellow>")
                )
                session_id = str(uuid.uuid4())[:8]
                display_welcome(session_id)
                continue
            elif command == "/resume":
                from openhands.sdk.conversation.state import AgentExecutionStatus
                from prompt_toolkit import print_formatted_text
                
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

            runner.process_message(message)

            print()  # Add spacing

        except KeyboardInterrupt:
            from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation
            from prompt_toolkit import print_formatted_text
            
            exit_confirmation = exit_session_confirmation()
            if exit_confirmation == UserConfirmation.ACCEPT:
                print_formatted_text(HTML("\n<yellow>Goodbye! 👋</yellow>"))
                _fast_exit()
                break
