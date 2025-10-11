"""End-to-end integration test for recursive file listing feature.

This test verifies the complete flow from API endpoint to actual file listing,
ensuring the recursive parameter works correctly through all layers.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from openhands.core.config import OpenHandsConfig
from openhands.events import EventStream
from openhands.llm.llm_registry import LLMRegistry
from openhands.runtime.impl.cli.cli_runtime import CLIRuntime
from openhands.server.session.conversation import ServerConversation


class TestRecursiveFileListingE2E:
    """Integration test for the complete recursive file listing flow."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with a known file structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file structure
            workspace = Path(tmpdir) / 'workspace'
            workspace.mkdir()

            # Create nested directory structure
            (workspace / 'src').mkdir()
            (workspace / 'src' / 'components').mkdir()
            (workspace / 'src' / 'utils').mkdir()
            (workspace / 'docs').mkdir()

            # Create test files
            (workspace / 'README.md').write_text('# Test Project')
            (workspace / 'package.json').write_text('{}')
            (workspace / 'src' / 'index.ts').write_text("console.log('test');")
            (workspace / 'src' / 'components' / 'Button.tsx').write_text(
                'export const Button = () => {};'
            )
            (workspace / 'src' / 'components' / 'Input.tsx').write_text(
                'export const Input = () => {};'
            )
            (workspace / 'src' / 'utils' / 'helpers.ts').write_text(
                'export const helper = () => {};'
            )
            (workspace / 'docs' / 'API.md').write_text('# API Documentation')

            yield workspace

    def test_cli_runtime_recursive_listing(self, temp_workspace):
        """Test that CLIRuntime correctly lists files recursively."""
        # Create a real CLIRuntime instance
        config = OpenHandsConfig()
        config.workspace_base = str(temp_workspace)

        event_stream = Mock(spec=EventStream)
        llm_registry = Mock(spec=LLMRegistry)

        runtime = CLIRuntime(
            config=config,
            event_stream=event_stream,
            llm_registry=llm_registry,
            sid='test-session',
        )

        # Initialize the runtime
        runtime._runtime_initialized = True
        runtime._workspace_path = str(temp_workspace)

        # Test non-recursive listing (should only get top-level items)
        non_recursive_files = runtime.list_files(recursive=False)

        # Should contain only top-level items
        assert any('README.md' in f for f in non_recursive_files)
        assert any('package.json' in f for f in non_recursive_files)
        assert any('src' in f for f in non_recursive_files)
        assert any('docs' in f for f in non_recursive_files)

        # Should NOT contain nested files
        assert not any('Button.tsx' in f for f in non_recursive_files)
        assert not any('helpers.ts' in f for f in non_recursive_files)

        print(f'✓ Non-recursive: Found {len(non_recursive_files)} top-level items')

        # Test recursive listing (should get ALL files)
        recursive_files = runtime.list_files(recursive=True)

        # Should contain top-level items
        assert any('README.md' in f for f in recursive_files)
        assert any('package.json' in f for f in recursive_files)

        # Should ALSO contain nested files
        assert any('Button.tsx' in f for f in recursive_files)
        assert any('Input.tsx' in f for f in recursive_files)
        assert any('helpers.ts' in f for f in recursive_files)
        assert any('API.md' in f for f in recursive_files)

        # Should have directories with trailing slashes
        assert any(f.endswith('src/') for f in recursive_files)
        assert any(f.endswith('components/') for f in recursive_files)

        print(f'✓ Recursive: Found {len(recursive_files)} total items (files + dirs)')

        # Verify recursive has more items than non-recursive
        assert len(recursive_files) > len(non_recursive_files), (
            'Recursive listing should return more items than non-recursive'
        )

    @pytest.mark.asyncio
    async def test_api_endpoint_to_runtime_flow(self, temp_workspace):
        """Test the complete flow from API endpoint to runtime."""
        from openhands.server.routes.files import list_files

        # Create a mock conversation with a real CLIRuntime
        config = OpenHandsConfig()
        config.workspace_base = str(temp_workspace)

        event_stream = Mock(spec=EventStream)
        llm_registry = Mock(spec=LLMRegistry)

        runtime = CLIRuntime(
            config=config,
            event_stream=event_stream,
            llm_registry=llm_registry,
            sid='test-session',
        )
        runtime._runtime_initialized = True
        runtime._workspace_path = str(temp_workspace)

        # Mock conversation
        conversation = Mock(spec=ServerConversation)
        conversation.runtime = runtime

        # Test the endpoint with recursive=False
        result = await list_files(conversation=conversation, path=None, recursive=False)

        assert isinstance(result, list)
        non_recursive_count = len(result)
        print(f'✓ API with recursive=False returned {non_recursive_count} items')

        # Test the endpoint with recursive=True
        result = await list_files(conversation=conversation, path=None, recursive=True)

        assert isinstance(result, list)
        recursive_count = len(result)
        print(f'✓ API with recursive=True returned {recursive_count} items')

        # Recursive should return more items
        assert recursive_count > non_recursive_count, (
            f'Expected recursive ({recursive_count}) > non-recursive ({non_recursive_count})'
        )

    def test_action_execution_client_sends_recursive_param(self):
        """Test that ActionExecutionClient always sends the recursive parameter."""
        from openhands.runtime.impl.action_execution.action_execution_client import (
            ActionExecutionClient,
        )

        # Create a mock client
        mock_client = Mock()
        mock_client.log = Mock()
        mock_client.action_execution_server_url = 'http://test'

        # Track what gets sent
        sent_data = {}

        def capture_request(*args, **kwargs):
            sent_data.update(kwargs.get('json', {}))
            response = Mock()
            response.json.return_value = []
            response.is_closed = True
            return response

        mock_client._send_action_server_request = capture_request

        # Test with recursive=False (the bug case)
        ActionExecutionClient.list_files(mock_client, recursive=False)
        assert sent_data.get('recursive') is False, 'recursive=False must be sent!'
        print('✓ ActionExecutionClient sends recursive=False')

        # Test with recursive=True
        sent_data.clear()
        ActionExecutionClient.list_files(mock_client, recursive=True)
        assert sent_data.get('recursive') is True, 'recursive=True must be sent!'
        print('✓ ActionExecutionClient sends recursive=True')

    def test_frontend_regex_preserves_decorators(self):
        """Test that the frontend regex doesn't strip code decorators."""
        # The regex from use-chat-submission.ts
        import re

        pattern = r'(^|\s)@((?:\.\/|\.\.\/|~\/)[^\s]*|[^\s]*\/[^\s]*|[^\s]+\.(?:ts|tsx|js|jsx|py|java|cpp|c|h|hpp|cs|rb|go|rs|md|txt|json|yaml|yml|xml|html|css|scss|sass|less|vue|svelte)(?:\s|$))'
        regex = re.compile(pattern, re.IGNORECASE)

        # Test file paths are stripped
        assert regex.sub(r'\1\2', '@src/file.py') == 'src/file.py'
        assert regex.sub(r'\1\2', 'Check @./README.md') == 'Check ./README.md'
        print('✓ Frontend strips @ from file paths')

        # Test decorators are preserved
        assert regex.sub(r'\1\2', '@property') == '@property'
        assert regex.sub(r'\1\2', '@dataclass') == '@dataclass'
        assert (
            regex.sub(r'\1\2', 'Use @Override annotation') == 'Use @Override annotation'
        )
        print('✓ Frontend preserves @ in code decorators')


@pytest.mark.integration
def test_full_recursive_listing_integration():
    """Run all integration tests to verify the complete feature works."""
    test = TestRecursiveFileListingE2E()

    # Create temp workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir) / 'workspace'
        workspace.mkdir()

        # Create test structure (matching what test expects)
        (workspace / 'src').mkdir()
        (workspace / 'src' / 'components').mkdir()
        (workspace / 'src' / 'utils').mkdir()
        (workspace / 'docs').mkdir()

        # Create test files
        (workspace / 'README.md').write_text('# Test Project')
        (workspace / 'package.json').write_text('{}')
        (workspace / 'src' / 'index.ts').write_text("console.log('test');")
        (workspace / 'src' / 'components' / 'Button.tsx').write_text(
            'export const Button = () => {};'
        )
        (workspace / 'src' / 'components' / 'Input.tsx').write_text(
            'export const Input = () => {};'
        )
        (workspace / 'src' / 'utils' / 'helpers.ts').write_text(
            'export const helper = () => {};'
        )
        (workspace / 'docs' / 'API.md').write_text('# API Documentation')

        print('\n=== Running Integration Tests ===\n')

        # Test CLIRuntime
        test.test_cli_runtime_recursive_listing(workspace)

        # Test ActionExecutionClient
        test.test_action_execution_client_sends_recursive_param()

        # Test Frontend regex
        test.test_frontend_regex_preserves_decorators()

        print('\n✅ All integration tests passed!')


if __name__ == '__main__':
    test_full_recursive_listing_integration()
