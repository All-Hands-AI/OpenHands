"""Modal runtime implementation."""

from pydantic import SecretStr

# Configuration specification for this runtime
CONFIG_SPEC = {
    'api_token_id': {
        'type': SecretStr,
        'default': None,
        'description': 'Modal API token ID for authentication'
    },
    'api_token_secret': {
        'type': SecretStr,
        'default': None,
        'description': 'Modal API token secret for authentication'
    }
}