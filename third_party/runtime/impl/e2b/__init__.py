"""E2B runtime implementation."""

from pydantic import SecretStr

# Configuration specification for this runtime
CONFIG_SPEC = {
    'api_key': {
        'type': SecretStr,
        'default': None,
        'description': 'E2B API key for authentication'
    }
}