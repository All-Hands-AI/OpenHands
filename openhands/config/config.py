"""Configuration module."""

import os
from typing import Any, Dict

import tomli


def get_config() -> Dict[str, Any]:
    """Get configuration from config file.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    config_path = os.environ.get('OPENHANDS_CONFIG_PATH', 'config.toml')

    if not os.path.exists(config_path):
        return {}

    with open(config_path, 'rb') as f:
        return tomli.load(f)


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """Get a configuration value.

    Args:
        section: Configuration section.
        key: Configuration key.
        default: Default value if not found.

    Returns:
        Any: Configuration value or default.
    """
    config = get_config()
    section_config = config.get(section, {})
    return section_config.get(key, default)
