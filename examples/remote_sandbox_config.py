#!/usr/bin/env python3
"""
Example configuration for using RemoteSandboxService in OpenHands.

This shows how to configure the app server to use a remote sandbox service
instead of the default Docker-based sandbox service.
"""

import os

from openhands.app_server.config import AppServerConfig
from openhands.app_server.sandbox.remote_sandbox_service import (
    RemoteSandboxConfig,
    RemoteSandboxServiceManager,
)


def create_remote_sandbox_config() -> AppServerConfig:
    """Create app server config with remote sandbox service."""

    # Configuration for remote sandbox service
    remote_config = RemoteSandboxConfig(
        remote_runtime_api_url=os.getenv(
            'REMOTE_RUNTIME_API_URL', 'http://localhost:8080'
        ),
        api_key=os.getenv('REMOTE_RUNTIME_API_KEY', 'your-api-key'),
        container_url_pattern=os.getenv(
            'CONTAINER_URL_PATTERN', 'http://localhost:{port}'
        ),
        request_timeout=int(os.getenv('REMOTE_RUNTIME_TIMEOUT', '300')),
    )

    # Create sandbox service manager
    sandbox_manager = RemoteSandboxServiceManager(config=remote_config)

    # Create app server config
    config = AppServerConfig()
    config.sandbox = sandbox_manager

    return config


def main():
    """Example usage."""
    print('Creating remote sandbox configuration...')

    config = create_remote_sandbox_config()

    print(f'Remote runtime API URL: {config.sandbox.config.remote_runtime_api_url}')
    print(f'Request timeout: {config.sandbox.config.request_timeout}s')

    print('\nTo use this configuration:')
    print('1. Set environment variables:')
    print('   export REMOTE_RUNTIME_API_URL=http://your-runtime-server.com')
    print('   export REMOTE_RUNTIME_API_KEY=your-api-key')
    print('   export CONTAINER_URL_PATTERN=http://localhost:{port}')
    print('   export REMOTE_RUNTIME_TIMEOUT=300')
    print('')
    print('2. Modify openhands/app_server/config.py sandbox_manager() function')
    print(
        '   to return RemoteSandboxServiceManager instead of DockerSandboxServiceManager'
    )
    print('')
    print('3. Start the OpenHands app server as usual')


if __name__ == '__main__':
    main()
