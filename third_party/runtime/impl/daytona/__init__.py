"""Daytona runtime implementation."""

from pydantic import SecretStr

# Configuration specification for this runtime
CONFIG_SPEC = {
    'api_key': {
        'type': SecretStr,
        'default': None,
        'description': 'Daytona API key for authentication'
    },
    'api_url': {
        'type': str,
        'default': 'https://app.daytona.io/api',
        'description': 'Daytona API URL endpoint'
    },
    'target': {
        'type': str,
        'default': 'eu',
        'description': 'Daytona target region'
    }
}