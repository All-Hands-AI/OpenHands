"""
Shared command handlers for openhands-cli.
These commands are available in both TUI mode and ACP mode.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class CommandResult(Enum):
    """Result of executing a command."""

    CONTINUE = "continue"  # Continue the conversation loop
    EXIT = "exit"  # Exit the conversation
    HANDLED = "handled"  # Command was handled, continue loop


@dataclass
class Command:
    """Definition of a slash command."""

    name: str
    description: str
    handler: Callable | None = None
    input_hint: str | None = None  # For commands that take input


# Available commands in OpenHands CLI
AVAILABLE_COMMANDS = [
    Command(
        name="help",
        description="Show available commands and usage information",
        input_hint=None,
    ),
    Command(
        name="exit",
        description="Exit the current conversation session",
        input_hint=None,
    ),
    Command(
        name="clear",
        description="Clear the screen and start fresh",
        input_hint=None,
    ),
    Command(
        name="settings",
        description="Open agent configuration settings",
        input_hint=None,
    ),
    Command(
        name="mcp",
        description="View MCP server information and status",
        input_hint=None,
    ),
    Command(
        name="status",
        description="Show current conversation status and settings",
        input_hint=None,
    ),
    Command(
        name="confirm",
        description="Toggle confirmation mode for agent actions",
        input_hint=None,
    ),
    Command(
        name="resume",
        description="Resume a paused conversation",
        input_hint=None,
    ),
]


def get_acp_available_commands() -> list[dict]:
    """
    Get available commands in ACP format.

    Returns:
        List of command dictionaries for ACP protocol
    """
    acp_commands = []
    for cmd in AVAILABLE_COMMANDS:
        acp_cmd = {
            "name": cmd.name,
            "description": cmd.description,
        }
        if cmd.input_hint:
            acp_cmd["input"] = {"hint": cmd.input_hint}
        acp_commands.append(acp_cmd)

    return acp_commands


def is_slash_command(text: str) -> bool:
    """Check if the text is a slash command."""
    return text.strip().startswith("/")


def parse_slash_command(text: str) -> tuple[str, str]:
    """
    Parse a slash command into command name and arguments.

    Args:
        text: Command text (e.g., "/help" or "/web search query")

    Returns:
        Tuple of (command_name, arguments)
    """
    text = text.strip()
    if not text.startswith("/"):
        return "", text

    # Remove leading slash
    text = text[1:]

    # Split into command and args
    parts = text.split(None, 1)
    command = parts[0].lower() if parts else ""
    args = parts[1] if len(parts) > 1 else ""

    return command, args


def format_help_text() -> str:
    """Format help text with all available commands."""
    lines = [
        "Available Commands:",
        "",
    ]

    for cmd in AVAILABLE_COMMANDS:
        if cmd.input_hint:
            lines.append(f"  /{cmd.name} <{cmd.input_hint}>")
        else:
            lines.append(f"  /{cmd.name}")
        lines.append(f"    {cmd.description}")
        lines.append("")

    return "\n".join(lines)
