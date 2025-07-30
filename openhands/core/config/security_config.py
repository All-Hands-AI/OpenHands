import re
import shlex
from typing import Pattern

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ApprovedCommandPattern(BaseModel):
    """Configuration for an approved command pattern.

    Attributes:
        pattern: The regex pattern to match commands against.
        description: A human-readable description of what this pattern matches.
    """

    pattern: str
    description: str

    @property
    def compiled_pattern(self) -> Pattern:
        """Return the compiled regex pattern."""
        return re.compile(self.pattern)

    def matches(self, command: str) -> bool:
        """Check if the command matches this pattern."""
        return bool(self.compiled_pattern.match(command))


class SecurityConfig(BaseModel):
    """Configuration for security related functionalities.

    Attributes:
        confirmation_mode: Whether to enable confirmation mode.
        security_analyzer: The security analyzer to use.
        approved_command_patterns: List of approved command patterns that don't require confirmation.
        approved_commands: Dictionary of exact commands that have been approved.
    """

    confirmation_mode: bool = Field(default=False)
    security_analyzer: str | None = Field(default=None)
    approved_command_patterns: list[ApprovedCommandPattern] = Field(
        default_factory=list
    )
    approved_commands: dict[str, bool] = Field(default_factory=dict)

    model_config = ConfigDict(extra='forbid')

    def _parse_piped_command(self, command: str) -> list[str]:
        """Parse a command that may contain pipes into individual commands.

        Args:
            command: The command string to parse.

        Returns:
            list[str]: List of individual commands split by pipes.
        """
        # Handle edge cases first
        if not command or not command.strip():
            return []

        # Check for invalid pipe patterns
        if command.strip().startswith('|') or command.strip().endswith('|'):
            return []  # Invalid: starts or ends with pipe

        if '||' in command:
            return []  # Invalid: double pipes

        # Split by pipe operator, handling quoted strings properly
        parts = []
        current_part: list[str] = []

        # Use shlex to properly handle quoted strings and escapes
        try:
            tokens = shlex.split(command, posix=True)
        except ValueError:
            # If shlex fails (e.g., unmatched quotes), fall back to simple split
            tokens = command.split()

        # Reconstruct the command while splitting on pipes
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '|':
                if current_part:
                    parts.append(' '.join(current_part))
                    current_part = []
                else:
                    # Empty part before pipe - invalid
                    return []
            else:
                current_part.append(token)
            i += 1

        # Add the last part if it exists
        if current_part:
            parts.append(' '.join(current_part))
        elif parts:  # We had pipes but no final command
            return []  # Invalid: ends with pipe

        # If no pipes were found, fall back to simple pipe splitting
        if len(parts) <= 1 and '|' in command:
            simple_parts = [part.strip() for part in command.split('|')]
            # Check for empty parts
            if any(not part for part in simple_parts):
                return []  # Invalid: empty parts
            parts = simple_parts

        return parts

    def _is_single_command_approved(self, command: str) -> bool:
        """Check if a single (non-piped) command is approved.

        Args:
            command: The single command to check.

        Returns:
            bool: True if the command is approved, False otherwise.
        """
        command = command.strip()

        # Check exact matches first
        if command in self.approved_commands:
            return self.approved_commands[command]

        # Then check patterns
        for pattern in self.approved_command_patterns:
            if pattern.matches(command):
                return True

        return False

    def is_command_approved(self, command: str) -> bool:
        """Check if a command is approved and doesn't need confirmation.

        This method handles both simple commands and piped commands.
        For piped commands, ALL individual commands must be approved.

        Args:
            command: The command to check (may contain pipes).

        Returns:
            bool: True if the command (and all sub-commands if piped) is approved, False otherwise.
        """
        # Handle empty or whitespace-only commands
        if not command or not command.strip():
            return False

        # Parse the command to handle pipes
        sub_commands = self._parse_piped_command(command)

        # If no valid sub-commands were parsed, reject
        if not sub_commands:
            return False

        # All sub-commands must be approved
        for sub_command in sub_commands:
            if not sub_command.strip():  # Skip empty sub-commands
                return False
            if not self._is_single_command_approved(sub_command):
                return False

        return True

    def approve_command(self, command: str) -> None:
        """Add a command to the approved commands list.

        Args:
            command: The command to approve.
        """
        self.approved_commands[command] = True

    def add_approved_pattern(self, pattern: str, description: str) -> None:
        """Add a pattern to the approved patterns list.

        Args:
            pattern: The regex pattern to add.
            description: A description of what this pattern matches.
        """
        self.approved_command_patterns.append(
            ApprovedCommandPattern(pattern=pattern, description=description)
        )

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'SecurityConfig']:
        """
        Create a mapping of SecurityConfig instances from a toml dictionary representing the [security] section.

        The configuration is built from all keys in data.

        Returns:
            dict[str, SecurityConfig]: A mapping where the key "security" corresponds to the [security] configuration
        """

        # Initialize the result mapping
        security_mapping: dict[str, SecurityConfig] = {}

        # Extract approved command patterns if present
        approved_patterns = []
        if 'approved_command_patterns' in data:
            patterns_data = data.pop('approved_command_patterns')
            if isinstance(patterns_data, list):
                for pattern_data in patterns_data:
                    if (
                        isinstance(pattern_data, dict)
                        and 'pattern' in pattern_data
                        and 'description' in pattern_data
                    ):
                        approved_patterns.append(
                            ApprovedCommandPattern(
                                pattern=pattern_data['pattern'],
                                description=pattern_data['description'],
                            )
                        )

        # Extract approved commands if present
        approved_commands = {}
        if 'approved_commands' in data:
            commands_data = data.pop('approved_commands')
            if isinstance(commands_data, dict):
                approved_commands = commands_data

        # Try to create the configuration instance
        try:
            config = cls.model_validate(data)
            config.approved_command_patterns = approved_patterns
            config.approved_commands = approved_commands
            security_mapping['security'] = config
        except ValidationError as e:
            raise ValueError(f'Invalid security configuration: {e}')

        return security_mapping
