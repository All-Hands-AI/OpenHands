"""
Gateway configuration loader for OpenHands CLI.
Handles loading and parsing of enterprise gateway configuration files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as tomllib  # type: ignore[no-redef]

_VALID_FIELDS: set[str] = {
    'gateway_provider',
    'gateway_auth_url',
    'gateway_auth_method',
    'gateway_auth_headers',
    'gateway_auth_body',
    'gateway_auth_token_path',
    'gateway_auth_expires_in_path',
    'gateway_auth_token_ttl',
    'gateway_token_header',
    'gateway_token_prefix',
    'gateway_auth_verify_ssl',
    'custom_headers',
    'extra_body_params',
}


def load_gateway_config(config_path: Path | str) -> dict[str, Any]:
    """Load gateway configuration from a TOML file.

    Args:
        config_path: Path to the gateway configuration file

    Returns:
        Dictionary containing gateway configuration

    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If the file cannot be parsed or is not a mapping
    """
    if isinstance(config_path, str):
        config_path = Path(config_path)

    config_path = config_path.expanduser()

    if not config_path.exists():
        raise FileNotFoundError(f"Gateway config file not found: {config_path}")

    if config_path.suffix.lower() not in {'.toml', '.tml'}:
        raise ValueError(f'Gateway configuration must be TOML: {config_path}')

    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f'Invalid TOML in gateway config file: {exc}') from exc

    if not isinstance(config, dict):
        raise ValueError('Gateway config must be a mapping/object')

    unknown_fields = set(config.keys()) - _VALID_FIELDS
    if unknown_fields:
        print(f'Warning: Unknown gateway config fields will be ignored: {unknown_fields}')

    return config


def expand_env_vars(config: dict[str, Any]) -> dict[str, Any]:
    """Expand environment variables in config values.

    Supports ${ENV:VAR_NAME} syntax in string values.

    Args:
        config: Gateway configuration dictionary

    Returns:
        Configuration with environment variables expanded
    """
    import os

    def expand_value(value: Any) -> Any:
        if isinstance(value, str):
            # Look for ${ENV:VAR_NAME} pattern
            pattern = r'\$\{ENV:([^}]+)\}'

            def replacer(match):
                var_name = match.group(1)
                env_value = os.environ.get(var_name)
                if env_value is None:
                    raise ValueError(f"Environment variable {var_name} is not set")
                return env_value

            return re.sub(pattern, replacer, value)
        elif isinstance(value, dict):
            return {k: expand_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [expand_value(v) for v in value]
        return value

    return expand_value(config)
