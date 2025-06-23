"""Dynamic configuration for third-party runtimes.

This module provides a mechanism to dynamically discover and configure
third-party runtime settings without hardcoding runtime names in the core configuration.
"""

import importlib
import pkgutil
from typing import Any, Optional

from pydantic import Field, SecretStr


def discover_third_party_runtime_configs() -> dict[str, dict[str, Any]]:
    """Discover configuration requirements for third-party runtimes.

    Returns:
        Dictionary mapping runtime names to their configuration field definitions.
    """
    configs = {}

    try:
        import third_party.runtime.impl

        # Discover all third-party runtime packages
        for finder, name, ispkg in pkgutil.iter_modules(
            third_party.runtime.impl.__path__
        ):
            if ispkg:
                try:
                    # Import the runtime module
                    runtime_module = importlib.import_module(
                        f'third_party.runtime.impl.{name}'
                    )

                    # Look for configuration requirements
                    config_spec = getattr(runtime_module, 'CONFIG_SPEC', None)
                    if config_spec:
                        configs[name] = config_spec
                    else:
                        # Default configuration patterns based on runtime name
                        configs[name] = _get_default_config_spec(name)

                except ImportError:
                    # Skip if runtime module can't be imported
                    continue

    except ImportError:
        # third_party package not available
        pass

    return configs


def _get_default_config_spec(runtime_name: str) -> dict[str, Any]:
    """Get default configuration specification for a runtime.

    Args:
        runtime_name: Name of the runtime

    Returns:
        Dictionary with default configuration field specifications
    """
    # Common patterns for different runtimes
    if runtime_name == 'e2b':
        return {
            'api_key': {
                'type': SecretStr,
                'default': None,
                'description': 'E2B API key',
            }
        }
    elif runtime_name == 'modal':
        return {
            'api_token_id': {
                'type': SecretStr,
                'default': None,
                'description': 'Modal API token ID',
            },
            'api_token_secret': {
                'type': SecretStr,
                'default': None,
                'description': 'Modal API token secret',
            },
        }
    elif runtime_name == 'runloop':
        return {
            'api_key': {
                'type': SecretStr,
                'default': None,
                'description': 'Runloop API key',
            }
        }
    elif runtime_name == 'daytona':
        return {
            'api_key': {
                'type': SecretStr,
                'default': None,
                'description': 'Daytona API key',
            },
            'api_url': {
                'type': str,
                'default': 'https://app.daytona.io/api',
                'description': 'Daytona API URL',
            },
            'target': {
                'type': str,
                'default': 'eu',
                'description': 'Daytona target region',
            },
        }
    else:
        # Generic pattern for unknown runtimes
        return {
            'api_key': {
                'type': SecretStr,
                'default': None,
                'description': f'{runtime_name.title()} API key',
            }
        }


def get_third_party_config_fields() -> dict[str, Any]:
    """Get dynamic configuration fields for third-party runtimes.

    Returns:
        Dictionary of field names to Field definitions for Pydantic model
    """
    fields = {}
    runtime_configs = discover_third_party_runtime_configs()

    for runtime_name, config_spec in runtime_configs.items():
        for field_name, field_spec in config_spec.items():
            # Create field name like "e2b_api_key", "modal_api_token_id", etc.
            full_field_name = f'{runtime_name}_{field_name}'

            # Create Pydantic Field
            field_type = field_spec.get('type', str)
            default_value = field_spec.get('default', None)
            description = field_spec.get('description', f'{runtime_name} {field_name}')

            if field_type is SecretStr:
                fields[full_field_name] = (
                    Optional[SecretStr],
                    Field(default=default_value, description=description),
                )
            elif field_type is str:
                fields[full_field_name] = (
                    field_type,
                    Field(default=default_value, description=description),
                )
            else:
                fields[full_field_name] = (
                    field_type,
                    Field(default=default_value, description=description),
                )

    return fields


def get_third_party_config_value(
    config_obj: Any, runtime_name: str, field_name: str
) -> Any:
    """Get a third-party configuration value from a config object.

    Args:
        config_obj: Configuration object (OpenHandsConfig instance)
        runtime_name: Name of the runtime (e.g., 'e2b', 'modal')
        field_name: Name of the field (e.g., 'api_key', 'api_token_id')

    Returns:
        Configuration value or None if not found
    """
    full_field_name = f'{runtime_name}_{field_name}'
    return getattr(config_obj, full_field_name, None)
