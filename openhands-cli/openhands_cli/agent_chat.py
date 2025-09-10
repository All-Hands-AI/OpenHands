#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import logging

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands.sdk import (
    Message,
    TextContent,
)
from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import setup_agent
from openhands_cli.tui import (
    CommandCompleter,
    display_help,
    display_welcome,
)
from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation

logger = logging.getLogger(__name__)


def run_cli_entry() -> None:
    """Run the agent chat session using the agent SDK.

    Raises:
        AgentSetupError: If agent setup fails
        KeyboardInterrupt: If user interrupts the session
        EOFError: If EOF is encountered
    """
    # Try to setup agent, but allow CLI to start even without API key
    conversation = None
    try:
        conversation = setup_agent()
    except Exception as e:
        if "No API key found" in str(e):
            print_formatted_text(HTML(f'<red>Warning: {e}</red>'))
            print_formatted_text(HTML('<yellow>Starting CLI in configuration mode. Use /settings to configure API key.</yellow>'))
            print_formatted_text('')
        else:
            # For other errors, still fail
            raise

    # Generate session ID
    import uuid

    session_id = str(uuid.uuid4())[:8]

    display_welcome(session_id)

    # Create prompt session with command completer
    session = PromptSession(completer=CommandCompleter())

    # Create conversation runner to handle state machine logic (only if we have a conversation)
    runner = ConversationRunner(conversation) if conversation else None

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = session.prompt(
                HTML('<gold>> </gold>'),
                multiline=False,
            )

            if not user_input.strip():
                continue

            # Handle commands
            command = user_input.strip().lower()

            message = Message(
                role='user',
                content=[TextContent(text=user_input)],
            )

            if command == '/exit':
                exit_confirmation = exit_session_confirmation()
                if exit_confirmation == UserConfirmation.ACCEPT:
                    print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
                    break
            elif command == '/clear':
                display_welcome(session_id)
                continue
            elif command == '/help':
                display_help()
                continue
            elif command == '/status':
                print_formatted_text(HTML(f'<grey>Session ID: {session_id}</grey>'))
                if conversation:
                    print_formatted_text(HTML('<grey>Status: Active</grey>'))
                    confirmation_status = (
                        'enabled' if conversation.state.confirmation_mode else 'disabled'
                    )
                    print_formatted_text(
                        HTML(f'<grey>Confirmation mode: {confirmation_status}</grey>')
                    )
                else:
                    print_formatted_text(HTML('<grey>Status: Configuration mode (no API key)</grey>'))
                continue
            elif command == '/confirm':
                if not runner:
                    print_formatted_text(HTML('<red>Agent not available. Please configure API key using /settings first.</red>'))
                    continue
                current_mode = runner.confirmation_mode
                runner.set_confirmation_mode(not current_mode)
                new_status = 'enabled' if not current_mode else 'disabled'
                print_formatted_text(
                    HTML(f'<yellow>Confirmation mode {new_status}</yellow>')
                )
                continue
            elif command == '/new':
                print_formatted_text(
                    HTML('<yellow>Starting new conversation...</yellow>')
                )
                session_id = str(uuid.uuid4())[:8]
                display_welcome(session_id)
                continue
            elif command == '/resume':
                if not conversation:
                    print_formatted_text(HTML('<red>Agent not available. Please configure API key using /settings first.</red>'))
                    continue
                if not conversation.state.agent_paused:
                    print_formatted_text(
                        HTML('<red>No paused conversation to resume...</red>')
                    )

                    continue

                # Resume without new message
                message = None
            elif command == '/settings':
                from openhands_cli.tui.settings_ui import run_settings_configuration
                run_settings_configuration()
                
                # Try to reinitialize agent if settings were updated
                if not conversation:
                    try:
                        conversation = setup_agent()
                        runner = ConversationRunner(conversation)
                        print_formatted_text(HTML('<green>Agent initialized successfully!</green>'))
                    except Exception as e:
                        if "No API key found" not in str(e):
                            print_formatted_text(HTML(f'<red>Failed to initialize agent: {e}</red>'))
                continue

            # Handle regular messages
            if not runner:
                print_formatted_text(HTML('<red>Agent not available. Please configure API key using /settings first.</red>'))
                continue

            runner.process_message(message)

            print()  # Add spacing

        except KeyboardInterrupt:
            exit_confirmation = exit_session_confirmation()
            if exit_confirmation == UserConfirmation.ACCEPT:
                print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
                break
            continue
