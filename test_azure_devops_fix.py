#!/usr/bin/env python3

"""
Test script to verify Azure DevOps repository cloning fix
"""

import asyncio
import os
import tempfile
from types import MappingProxyType
from unittest.mock import MagicMock

from pydantic import SecretStr

from openhands.core.config import OpenHandsConfig
from openhands.events.action import CmdRunAction
from openhands.events.observation import NullObservation
from openhands.events.stream import EventStream
from openhands.integrations.provider import ProviderToken, ProviderType
from openhands.integrations.service_types import Repository
from openhands.runtime.base import Runtime
from openhands.storage import get_file_store


class TestRuntime(Runtime):
    """A concrete implementation of Runtime for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_action_calls = []

    async def connect(self):
        pass

    def close(self):
        pass

    def browse(self, action):
        return NullObservation(content='')

    def browse_interactive(self, action):
        return NullObservation(content='')

    def run(self, action):
        return NullObservation(content='')

    def run_ipython(self, action):
        return NullObservation(content='')

    def read(self, action):
        return NullObservation(content='')

    def write(self, action):
        return NullObservation(content='')

    def copy_from(self, path):
        return ''

    def copy_to(self, path, content):
        pass

    def list_files(self, path):
        return []

    def run_action(self, action) -> NullObservation:
        self.run_action_calls.append(action)
        return NullObservation(content='')

    def call_tool_mcp(self, action):
        return NullObservation(content='')

    def edit(self, action):
        return NullObservation(content='')

    def get_mcp_config(self, extra_stdio_servers=None):
        from openhands.core.config.mcp_config import MCPConfig
        return MCPConfig()


async def test_azure_devops_clone_url_construction():
    """Test that Azure DevOps clone URLs are constructed correctly"""
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        config = OpenHandsConfig()
        file_store = get_file_store('local', temp_dir)
        event_stream = EventStream('test', file_store)
        
        # Set up Azure DevOps token with host
        azure_devops_token = 'test-azure-token'
        azure_devops_host = 'https://dev.azure.com/all-hands-ai'
        git_provider_tokens = MappingProxyType({
            ProviderType.AZURE_DEVOPS: ProviderToken(
                token=SecretStr(azure_devops_token),
                host=azure_devops_host
            )
        })
        
        runtime = TestRuntime(
            config=config,
            event_stream=event_stream,
            sid='test',
            user_id='test_user',
            git_provider_tokens=git_provider_tokens,
        )
        
        # Mock the provider handler to return an Azure DevOps repository
        async def mock_verify_repo_provider(*args, **kwargs):
            return Repository(
                id='123',
                full_name='test-project/test-project',
                git_provider=ProviderType.AZURE_DEVOPS,
                is_public=False
            )
        
        # Patch the verify_repo_provider method
        from openhands.integrations.provider import ProviderHandler
        original_method = ProviderHandler.verify_repo_provider
        ProviderHandler.verify_repo_provider = mock_verify_repo_provider
        
        try:
            # Test cloning with Azure DevOps repository
            result = await runtime.clone_or_init_repo(
                git_provider_tokens, 
                'test-project/test-project', 
                None
            )
            
            # Verify that git clone and checkout were called
            assert len(runtime.run_action_calls) == 2
            assert isinstance(runtime.run_action_calls[0], CmdRunAction)
            assert isinstance(runtime.run_action_calls[1], CmdRunAction)
            
            # Check the clone command
            clone_cmd = runtime.run_action_calls[0].command
            print(f"Clone command: {clone_cmd}")
            
            # The expected URL format for Azure DevOps:
            # https://token@dev.azure.com/organization/project/_git/repository
            expected_url = f'https://{azure_devops_token}@dev.azure.com/all-hands-ai/test-project/_git/test-project'
            assert expected_url in clone_cmd
            
            # Check the checkout command
            checkout_cmd = runtime.run_action_calls[1].command
            print(f"Checkout command: {checkout_cmd}")
            assert 'cd test-project' in checkout_cmd
            assert 'git checkout -b openhands-workspace-' in checkout_cmd
            
            assert result == 'test-project'
            
            print("✅ Azure DevOps clone URL construction test PASSED")
            
        finally:
            # Restore the original method
            ProviderHandler.verify_repo_provider = original_method


async def test_azure_devops_environment_setup():
    """Test that Azure DevOps environment variables are handled correctly"""
    
    # Test the setup.py logic
    from openhands.core.setup import initialize_repository_for_runtime
    
    # Set environment variables
    os.environ['AZURE_DEVOPS_TOKEN'] = 'test-token'
    os.environ['AZURE_DEVOPS_HOST'] = 'https://dev.azure.com/all-hands-ai'
    
    try:
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OpenHandsConfig()
            file_store = get_file_store('local', temp_dir)
            event_stream = EventStream('test', file_store)
            
            runtime = TestRuntime(
                config=config,
                event_stream=event_stream,
                sid='test',
                user_id='test_user',
            )
            
            # Mock the clone_or_init_repo method to capture the tokens
            captured_tokens = None
            
            async def mock_clone_or_init_repo(tokens, repo, branch):
                nonlocal captured_tokens
                captured_tokens = tokens
                return 'test-repo'
            
            runtime.clone_or_init_repo = mock_clone_or_init_repo
            
            # Call initialize_repository_for_runtime
            result = initialize_repository_for_runtime(runtime, 'test-project/test-project')
            
            # Verify that the Azure DevOps token was set up correctly
            assert captured_tokens is not None
            assert ProviderType.AZURE_DEVOPS in captured_tokens
            
            azure_token = captured_tokens[ProviderType.AZURE_DEVOPS]
            assert azure_token.token.get_secret_value() == 'test-token'
            assert azure_token.host == 'https://dev.azure.com/all-hands-ai'
            
            print("✅ Azure DevOps environment setup test PASSED")
            
    finally:
        # Clean up environment variables
        if 'AZURE_DEVOPS_TOKEN' in os.environ:
            del os.environ['AZURE_DEVOPS_TOKEN']
        if 'AZURE_DEVOPS_HOST' in os.environ:
            del os.environ['AZURE_DEVOPS_HOST']


async def main():
    """Run all tests"""
    print("Testing Azure DevOps repository cloning fixes...")
    
    await test_azure_devops_clone_url_construction()
    await test_azure_devops_environment_setup()
    
    print("\n🎉 All Azure DevOps tests PASSED!")


if __name__ == '__main__':
    asyncio.run(main())