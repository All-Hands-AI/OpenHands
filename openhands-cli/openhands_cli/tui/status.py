"""Status display components for OpenHands CLI TUI."""

from datetime import datetime

from openhands.sdk import BaseConversation
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.widgets import Frame, TextArea


def display_status(
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
    _display_usage_metrics_container(
        total_cost,
        total_input_tokens,
        total_output_tokens,
        cache_hits,
        cache_writes,
        total_tokens
    )


def _display_usage_metrics_container(
    total_cost: float,
    total_input_tokens: int,
    total_output_tokens: int,
    cache_hits: int,
    cache_writes: int,
    total_tokens: int
) -> None:
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
