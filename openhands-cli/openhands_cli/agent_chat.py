#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import sys
from datetime import datetime

from openhands.sdk import (
    Message,
    TextContent,
)
from openhands.sdk.conversation.state import AgentExecutionStatus
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import MissingAgentSpec, setup_conversation, start_fresh_conversation
from openhands_cli.tui.settings.mcp_screen import MCPScreen
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.tui.status import display_status
from openhands_cli.tui.tui import (
    display_help,
    display_welcome,
)
from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation
from openhands_cli.user_actions.utils import get_session_prompter


def _restore_tty() -> None:
    """
    Ensure terminal modes are reset in case prompt_toolkit cleanup didn't run.
    - Turn off application cursor keys (DECCKM): ESC[?1l
    - Turn off bracketed paste: ESC[?2004l
    """
    try:
        sys.stdout.write('\x1b[?1l\x1b[?2004l')
        sys.stdout.flush()
    except Exception:
        pass


def _print_exit_hint(conversation_id: str) -> None:
    """Print a resume hint with the current conversation ID."""
    print_formatted_text(
        HTML(f'<grey>Conversation ID:</grey> <yellow>{conversation_id}</yellow>')
    )
    print_formatted_text(
        HTML(
            f'<grey>Hint:</grey> run <gold>openhands --resume {conversation_id}</gold> '
            'to resume this conversation.'
        )
    )



def run_cli_entry(resume_conversation_id: str | None = None) -> None:
    """Run the agent chat session using the agent SDK.


    Raises:
        AgentSetupError: If agent setup fails
        KeyboardInterrupt: If user interrupts the session
        EOFError: If EOF is encountered
    """

    try:
        conversation = start_fresh_conversation(resume_conversation_id)
    except MissingAgentSpec:
        print_formatted_text(HTML('\n<yellow>Setup is required to use OpenHands CLI.</yellow>'))
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
        return


    display_welcome(conversation.id, bool(resume_conversation_id))

    # Track session start time for uptime calculation
    session_start_time = datetime.now()

    # Create conversation runner to handle state machine logic
    runner = ConversationRunner(conversation)
    session = get_session_prompter()

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
                    _print_exit_hint(conversation.id)
                    break

            elif command == '/settings':
                settings_screen = SettingsScreen(conversation)
                settings_screen.display_settings()
                continue

            elif command == '/mcp':
                mcp_screen = MCPScreen()
                mcp_screen.display_mcp_info(conversation.agent)
                continue

            elif command == '/clear':
                display_welcome(conversation.id)
                continue

            elif command == '/new':
                try:
                    # Start a fresh conversation (no resume ID = new conversation)
                    conversation = setup_conversation()
                    runner = ConversationRunner(conversation)
                    display_welcome(conversation.id, resume=False)
                    print_formatted_text(
                        HTML('<green>✓ Started fresh conversation</green>')
                    )
                    continue
                except Exception as e:
                    print_formatted_text(
                        HTML(f'<red>Error starting fresh conversation: {e}</red>')
                    )
                    continue

            elif command == '/help':
                display_help()
                continue

            elif command == '/status':
                display_status(conversation, session_start_time=session_start_time)
                continue

            elif command == '/confirm':
                runner.toggle_confirmation_mode()
                new_status = (
                    'enabled' if runner.is_confirmation_mode_active else 'disabled'
                )
                print_formatted_text(
                    HTML(f'<yellow>Confirmation mode {new_status}</yellow>')
                )
                continue

            elif command == '/resume':
                if not (
                    conversation.state.agent_status == AgentExecutionStatus.PAUSED
                    or conversation.state.agent_status
                    == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
                ):
                    print_formatted_text(
                        HTML('<red>No paused conversation to resume...</red>')
                    )
                    continue

                # Resume without new message
                message = None

            runner.process_message(message)

            print()  # Add spacing

        except KeyboardInterrupt:
            exit_confirmation = exit_session_confirmation()
            if exit_confirmation == UserConfirmation.ACCEPT:
                print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
                _print_exit_hint(conversation.id)
                break

    # Clean up terminal state
    _restore_tty()
