"""Runloop runtime implementation."""

from pydantic import SecretStr

# Configuration specification for this runtime
CONFIG_SPEC = {
    'api_key': {
        'type': SecretStr,
        'default': None,
        'description': 'Runloop API key for authentication'
    }
}