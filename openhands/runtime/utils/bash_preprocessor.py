"""
Bash command preprocessor for handling problematic shell options.

This module provides functionality to detect and transform bash commands that contain
problematic shell options like 'set -e', 'set -eu', or 'set -euo pipefail' which can
cause the bash session to exit unexpectedly when commands fail.
"""

import logging
import re

# Use standard Python logging, fallback if OpenHands logger not available
try:
    from openhands.core.logger import openhands_logger as logger
except ImportError:
    logger = logging.getLogger(__name__)


class BashCommandPreprocessor:
    """Preprocessor for bash commands to handle problematic shell options."""

    # Patterns to detect problematic set commands
    SET_E_PATTERNS = [
        # Direct set commands with -e option
        r'\bset\s+(?:-[a-zA-Z]*e[a-zA-Z]*|--errexit)\b',
        # set with multiple options containing 'e'
        r'\bset\s+-[a-zA-Z]*e[a-zA-Z]*\b',
        # set -o errexit
        r'\bset\s+-o\s+errexit\b',
    ]

    # Patterns to detect set commands with pipefail
    SET_PIPEFAIL_PATTERNS = [
        r'\bset\s+-o\s+pipefail\b',
        r'\bset\s+(?:-[a-zA-Z]*o[a-zA-Z]*\s+pipefail|--pipefail)\b',
    ]

    # Combined pattern for any problematic set command
    PROBLEMATIC_SET_PATTERN = re.compile(
        r'\bset\s+(?:'
        r'-[a-zA-Z]*[eu][a-zA-Z]*(?:\s+\w+)*(?:\s|;|&&|\|\||$)|'  # set -e, set -u, set -eu, etc.
        r'-o\s+(?:errexit|nounset|pipefail)(?:\s|;|&&|\|\||$)|'  # set -o errexit/nounset/pipefail
        r'--(?:errexit|nounset|pipefail)(?:\s|;|&&|\|\||$)'  # set --errexit/nounset/pipefail
        r')',
        re.IGNORECASE,
    )

    # Pattern to extract full set commands including all arguments
    FULL_SET_COMMAND_PATTERN = re.compile(
        r'\bset\s+(?:'
        r'-[a-zA-Z]*[eu][a-zA-Z]*(?:\s+\w+)*|'  # set -e, set -u, set -euo pipefail, etc.
        r'-o\s+(?:errexit|nounset|pipefail)|'  # set -o errexit/nounset/pipefail
        r'--(?:errexit|nounset|pipefail)'  # set --errexit/nounset/pipefail
        r')',
        re.IGNORECASE,
    )

    def __init__(self):
        """Initialize the preprocessor."""
        pass

    def is_problematic_command(self, command: str) -> bool:
        """
        Check if a command contains problematic set options.

        Args:
            command: The bash command to check

        Returns:
            True if the command contains problematic set options, False otherwise
        """
        if not command.strip():
            return False

        # Check for problematic set commands
        return bool(self.PROBLEMATIC_SET_PATTERN.search(command))

    def extract_set_commands(self, command: str) -> list[str]:
        """
        Extract all set commands from a bash command string.

        Args:
            command: The bash command to analyze

        Returns:
            List of set command strings found in the command
        """
        set_commands = []
        matches = self.FULL_SET_COMMAND_PATTERN.finditer(command)

        for match in matches:
            set_commands.append(match.group(0).strip())

        return set_commands

    def transform_command(self, command: str) -> tuple[str, bool]:
        """
        Transform a problematic command into a safer version.

        This method wraps commands containing problematic set options in a subshell
        to prevent them from affecting the main bash session.

        Args:
            command: The original bash command

        Returns:
            Tuple of (transformed_command, was_transformed)
        """
        if not self.is_problematic_command(command):
            return command, False

        logger.debug(f'Transforming problematic command: {command}')

        # Extract the set commands for logging
        set_commands = self.extract_set_commands(command)
        logger.info(f'Detected problematic set commands: {set_commands}')

        # Wrap the entire command in a subshell to isolate the set options
        # This prevents the set options from affecting the parent shell
        transformed = f'( {command} )'

        logger.debug(f'Transformed command: {transformed}')

        return transformed, True

    def get_warning_message(
        self, original_command: str, transformed_command: str
    ) -> str:
        """
        Generate a warning message about command transformation.

        Args:
            original_command: The original command
            transformed_command: The transformed command

        Returns:
            Warning message string
        """
        set_commands = self.extract_set_commands(original_command)

        return (
            f'[WARNING] Command contains problematic shell options: {", ".join(set_commands)}. '
            f'The command has been wrapped in a subshell to prevent session termination. '
            f'Original: {original_command.strip()} -> Transformed: {transformed_command.strip()}'
        )


# Global instance for easy access
bash_preprocessor = BashCommandPreprocessor()
