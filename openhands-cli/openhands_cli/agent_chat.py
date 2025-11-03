#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import sys
from datetime import datetime
import uuid

from openhands.sdk import (
    Message,
    TextContent,
)
from openhands.sdk.conversation.state import AgentExecutionStatus
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML

from openhands_cli.runner import ConversationRunner
from openhands_cli.process_runner import ProcessBasedConversationRunner
from openhands_cli.signal_handler import ProcessSignalHandler
from openhands_cli.setup import (
    MissingAgentSpec,
    setup_conversation,
    verify_agent_exists_or_setup_agent
)
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

    conversation_id = uuid.uuid4()
    if resume_conversation_id:
        try:
            conversation_id = uuid.UUID(resume_conversation_id)
        except ValueError as e:
            print_formatted_text(
                HTML(
                    f"<yellow>Warning: '{resume_conversation_id}' is not a valid UUID.</yellow>"
                )
            )
            return

    try:
        initialized_agent = verify_agent_exists_or_setup_agent()
    except MissingAgentSpec:
        print_formatted_text(HTML('\n<yellow>Setup is required to use OpenHands CLI.</yellow>'))
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
        return


    display_welcome(conversation_id, bool(resume_conversation_id))

    # Track session start time for uptime calculation
    session_start_time = datetime.now()

    # Create process-based conversation runner and signal handler
    process_runner = None
    signal_handler = ProcessSignalHandler()
    session = get_session_prompter()

    # Install signal handler for Ctrl+C management
    signal_handler.install_handler()

    try:
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
                        _print_exit_hint(conversation_id)
                        break

                elif command == '/settings':
                    # For process-based runner, we can't directly access the conversation
                    # TODO: Implement settings access through process communication if needed
                    settings_screen = SettingsScreen(None)
                    settings_screen.display_settings()
                    continue

                elif command == '/mcp':
                    mcp_screen = MCPScreen()
                    mcp_screen.display_mcp_info(initialized_agent)
                    continue

                elif command == '/clear':
                    display_welcome(conversation_id)
                    continue

                elif command == '/new':
                    try:
                        # Stop existing process runner if running
                        if process_runner:
                            process_runner.stop()
                            
                        # Start a fresh conversation with new process runner
                        process_runner = ProcessBasedConversationRunner(conversation_id, setup_conversation)
                        if process_runner.start():
                            signal_handler.set_conversation_process(process_runner.process)
                            display_welcome(conversation_id, resume=False)
                            print_formatted_text(
                                HTML('<green>✓ Started fresh conversation</green>')
                            )
                        else:
                            print_formatted_text(
                                HTML('<red>Failed to start fresh conversation</red>')
                            )
                            process_runner = None
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
                    if process_runner:
                        status = process_runner.get_status()
                        if status:
                            # Display status using the retrieved information
                            print_formatted_text(HTML(f'<yellow>Agent Status:</yellow> {status.get("agent_status", "Unknown")}'))
                            print_formatted_text(HTML(f'<yellow>Confirmation Mode:</yellow> {"Enabled" if status.get("confirmation_mode") else "Disabled"}'))
                            print_formatted_text(HTML(f'<yellow>Process Alive:</yellow> {process_runner.is_alive()}'))
                        else:
                            print_formatted_text(HTML('<red>Unable to get conversation status</red>'))
                    else:
                        print_formatted_text(HTML('<yellow>No active conversation</yellow>'))
                    continue

                elif command == '/confirm':
                    if process_runner:
                        result = process_runner.toggle_confirmation_mode()
                        if result:
                            print_formatted_text(HTML(f'<yellow>{result}</yellow>'))
                        else:
                            print_formatted_text(HTML('<red>Failed to toggle confirmation mode</red>'))
                    else:
                        print_formatted_text(HTML('<yellow>No active conversation</yellow>'))
                    continue

                elif command == '/resume':
                    if not process_runner:
                        print_formatted_text(
                            HTML('<yellow>No active conversation running...</yellow>')
                        )
                        continue

                    status = process_runner.get_status()
                    if not status:
                        print_formatted_text(
                            HTML('<red>Unable to get conversation status</red>')
                        )
                        continue
                        
                    agent_status = status.get("agent_status")
                    if not (
                        agent_status == AgentExecutionStatus.PAUSED
                        or agent_status == AgentExecutionStatus.WAITING_FOR_CONFIRMATION
                    ):
                        print_formatted_text(
                            HTML('<red>No paused conversation to resume...</red>')
                        )
                        continue

                    # Resume without new message
                    if process_runner.resume():
                        print_formatted_text(HTML('<green>Conversation resumed</green>'))
                    else:
                        print_formatted_text(HTML('<red>Failed to resume conversation</red>'))
                    continue

                # Create process runner if it doesn't exist
                if not process_runner:
                    process_runner = ProcessBasedConversationRunner(conversation_id, setup_conversation)
                    if not process_runner.start():
                        print_formatted_text(HTML('<red>Failed to start conversation process</red>'))
                        continue
                    signal_handler.set_conversation_process(process_runner.process)
                
                # Process the message
                if process_runner.process_message(message):
                    print()  # Add spacing for successful processing
                else:
                    print_formatted_text(HTML('<red>Failed to process message</red>'))

            except KeyboardInterrupt:
                # KeyboardInterrupt should be handled by the signal handler now
                # This is a fallback in case the signal handler doesn't catch it
                exit_confirmation = exit_session_confirmation()
                if exit_confirmation == UserConfirmation.ACCEPT:
                    print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
                    _print_exit_hint(conversation_id)
                    break
            except Exception as e:
                print_formatted_text(HTML(f'<red>Error in chat loop: {e}</red>'))
                continue

    except KeyboardInterrupt:
        # Final fallback for KeyboardInterrupt
        print_formatted_text(HTML('\n<yellow>Goodbye! 👋</yellow>'))
        _print_exit_hint(conversation_id)

    finally:
        # Clean up resources
        if process_runner:
            process_runner.stop()
        signal_handler.uninstall_handler()
        
        # Clean up terminal state
        _restore_tty()
