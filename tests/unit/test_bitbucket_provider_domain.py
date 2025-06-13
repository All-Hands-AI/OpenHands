import unittest
from unittest.mock import MagicMock, patch

from openhands.integrations.service_types import ProviderType, Repository
from openhands.runtime.base import Runtime


class TestBitbucketProviderDomain(unittest.TestCase):
    """Test that Bitbucket provider domain is properly handled in Runtime.clone_or_init_repo."""

    @patch('openhands.runtime.base.ProviderHandler')
    @patch.object(Runtime, 'run_action')
    async def test_bitbucket_provider_domain(
        self, mock_run_action, mock_provider_handler
    ):
        # Mock the provider handler to return a repository with Bitbucket as the provider
        mock_repository = Repository(
            id=1,
            full_name='test/repo',
            git_provider=ProviderType.BITBUCKET,
            is_public=True,
        )

        mock_provider_instance = MagicMock()
        mock_provider_instance.verify_repo_provider.return_value = mock_repository
        mock_provider_handler.return_value = mock_provider_instance

        # Create a minimal runtime instance
        runtime = Runtime(config=MagicMock(), event_stream=MagicMock(), sid='test_sid')

        # Mock the workspace_root property to avoid AttributeError
        runtime.workspace_root = '/workspace'

        # Call clone_or_init_repo with a Bitbucket repository
        # This should now succeed with our fix
        await runtime.clone_or_init_repo(
            git_provider_tokens=None,
            selected_repository='test/repo',
            selected_branch=None,
        )

        # Verify that run_action was called at least once (for git clone)
        self.assertTrue(mock_run_action.called)

        # Verify that the domain used was 'bitbucket.org'
        # Extract the command from the first call to run_action
        args, _ = mock_run_action.call_args
        action = args[0]
        self.assertIn('bitbucket.org', action.command)


if __name__ == '__main__':
    unittest.main()
