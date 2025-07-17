"""
MCP input validation functions for CLI.

This module provides validation functions for various MCP server configuration inputs
to ensure data integrity and provide clear error messages to users.
"""

import re
from urllib.parse import urlparse


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL format for MCP servers.

    Args:
        url: The URL string to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not url.strip():
        return False, 'URL cannot be empty'

    try:
        parsed = urlparse(url.strip())
        if not parsed.scheme:
            return False, 'URL must include a scheme (http:// or https://)'
        if not parsed.netloc:
            return False, 'URL must include a valid domain/host'
        if parsed.scheme not in ['http', 'https']:
            return False, 'URL scheme must be http or https'
        return True, ''
    except Exception as e:
        return False, f'Invalid URL format: {str(e)}'


def validate_server_name(name: str, existing_names: list[str]) -> tuple[bool, str]:
    """Validate server name for stdio MCP servers.

    Args:
        name: The server name to validate
        existing_names: List of existing server names to check for duplicates

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not name.strip():
        return False, 'Server name cannot be empty'

    name = name.strip()

    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return (
            False,
            'Server name can only contain letters, numbers, hyphens, and underscores',
        )

    # Check for duplicates
    if name in existing_names:
        return False, f"Server name '{name}' already exists"

    return True, ''


def validate_command(command: str) -> tuple[bool, str]:
    """Validate command for stdio MCP servers.

    Args:
        command: The command string to validate

    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if not command.strip():
        return False, 'Command cannot be empty'

    command = command.strip()

    # Check that command doesn't contain spaces (should be a single executable)
    if ' ' in command:
        return (
            False,
            'Command should be a single executable without spaces (use arguments field for parameters)',
        )

    return True, ''


def validate_args(args_input: str) -> tuple[bool, str, list[str]]:
    """Validate and parse arguments for stdio MCP servers.

    Args:
        args_input: Comma-separated arguments string

    Returns:
        tuple[bool, str, list[str]]: (is_valid, error_message, parsed_args)
    """
    if not args_input.strip():
        return True, '', []

    try:
        args = [arg.strip() for arg in args_input.split(',') if arg.strip()]
        return True, '', args
    except Exception as e:
        return False, f'Error parsing arguments: {str(e)}', []


def validate_env_vars(env_input: str) -> tuple[bool, str, dict[str, str]]:
    """Validate and parse environment variables for stdio MCP servers.

    Args:
        env_input: Comma-separated environment variables in KEY=VALUE format

    Returns:
        tuple[bool, str, dict[str, str]]: (is_valid, error_message, parsed_env)
    """
    if not env_input.strip():
        return True, '', {}

    env = {}
    try:
        for env_pair in env_input.split(','):
            env_pair = env_pair.strip()
            if not env_pair:
                continue

            if '=' not in env_pair:
                return (
                    False,
                    f"Invalid environment variable format: '{env_pair}'. Use KEY=VALUE format",
                    {},
                )

            key, value = env_pair.split('=', 1)
            key = key.strip()
            value = value.strip()

            if not key:
                return False, 'Environment variable key cannot be empty', {}

            # Validate environment variable name (basic validation)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                return (
                    False,
                    f"Invalid environment variable name: '{key}'. Must start with letter or underscore, contain only letters, numbers, and underscores",
                    {},
                )

            env[key] = value

        return True, '', env
    except Exception as e:
        return False, f'Error parsing environment variables: {str(e)}', {}
