#!/usr/bin/env python3
"""
Agent chat functionality for OpenHands CLI.
Provides a conversation interface with an AI agent using OpenHands patterns.
"""

import sys
from datetime import datetime

from openhands.sdk import (
    BaseConversation,
    Message,
    TextContent,
)
from openhands.sdk.conversation.state import AgentExecutionStatus
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea

from openhands_cli.runner import ConversationRunner
from openhands_cli.setup import MissingAgentSpec, setup_conversation
from openhands_cli.tui.settings.mcp_screen import MCPScreen
from openhands_cli.tui.settings.settings_screen import SettingsScreen
from openhands_cli.tui.tui import (
    display_help,
    display_welcome,
)
from openhands_cli.user_actions import UserConfirmation, exit_session_confirmation
from openhands_cli.user_actions.utils import get_session_prompter


def _display_status(
    conversation: BaseConversation, 
    session_start_time: datetime,
) -> None:
    """Display detailed conversation status including metrics and uptime.
    
    Args:
        conversation: The conversation to display status for
        session_start_time: The session start time for uptime calculation
    """
    # Get conversation stats
    stats = conversation.conversation_stats.get_combined_metrics()
    
    # Calculate uptime from session start time
    now = datetime.now()
    diff = now - session_start_time
    
    # Format as hours, minutes, seconds
    total_seconds = int(diff.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    
    # Display conversation ID and uptime
    print_formatted_text(HTML(f'<grey>Conversation ID: {conversation.id}</grey>'))
    print_formatted_text(HTML(f'<grey>Uptime:          {uptime_str}</grey>'))
    print_formatted_text('')
    
    # Calculate token metrics
    token_usage = stats.accumulated_token_usage
    total_input_tokens = token_usage.prompt_tokens if token_usage else 0
    total_output_tokens = token_usage.completion_tokens if token_usage else 0
    cache_hits = token_usage.cache_read_tokens if token_usage else 0
    cache_writes = token_usage.cache_write_tokens if token_usage else 0
    total_tokens = total_input_tokens + total_output_tokens
    total_cost = stats.accumulated_cost
    
    # Use prompt_toolkit containers for formatted display
    _display_usage_metrics_container(total_cost, total_input_tokens, total_output_tokens, 
                                   cache_hits, cache_writes, total_tokens)


def _display_usage_metrics_container(total_cost: float, total_input_tokens: int, total_output_tokens: int,
                                   cache_hits: int, cache_writes: int, total_tokens: int) -> None:
    """Display usage metrics using prompt_toolkit containers."""
    # Format values with proper formatting
    cost_str = f'${total_cost:.6f}'
    input_tokens_str = f'{total_input_tokens:,}'
    cache_read_str = f'{cache_hits:,}'
    cache_write_str = f'{cache_writes:,}'
    output_tokens_str = f'{total_output_tokens:,}'
    total_tokens_str = f'{total_tokens:,}'

    labels_and_values = [
        ('   Total Cost (USD):', cost_str),
        ('', ''),
        ('   Total Input Tokens:', input_tokens_str),
        ('      Cache Hits:', cache_read_str),
        ('      Cache Writes:', cache_write_str),
        ('   Total Output Tokens:', output_tokens_str),
        ('', ''),
        ('   Total Tokens:', total_tokens_str),
    ]

    # Calculate max widths for alignment
    max_label_width = max(len(label) for label, _ in labels_and_values)
    max_value_width = max(len(value) for _, value in labels_and_values)

    # Construct the summary text with aligned columns
    summary_lines = [
        f'{label:<{max_label_width}} {value:<{max_value_width}}'
        for label, value in labels_and_values
    ]
    summary_text = '\n'.join(summary_lines)

    container = Frame(
        TextArea(
            text=summary_text,
            read_only=True,
            wrap_lines=True,
        ),
        title='Usage Metrics',
    )

    print_container(container)



def _start_fresh_conversation(resume_conversation_id: str | None = None) -> BaseConversation:
    """Start a fresh conversation by creating a new conversation instance.
    
    Handles the complete conversation setup process including settings screen
    if agent configuration is missing.

    Args:
        resume_conversation_id: Optional conversation ID to resume

    Returns:
        BaseConversation: A new conversation instance
    """
    conversation = None
    settings_screen = SettingsScreen()

    while not conversation:
        try:
            conversation = setup_conversation(resume_conversation_id)
        except MissingAgentSpec:
            settings_screen.handle_basic_settings(escapable=False)
    
    return conversation


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

    conversation = _start_fresh_conversation(resume_conversation_id)
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
                    conversation = _start_fresh_conversation()
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
                _display_status(conversation, session_start_time=session_start_time)
                continue

            elif command == '/confirm':
                runner.toggle_confirmation_mode()
                new_status = (
                    'enabled' if runner.is_confirmation_mode_enabled else 'disabled'
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
