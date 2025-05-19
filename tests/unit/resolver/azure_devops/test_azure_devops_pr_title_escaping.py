from unittest.mock import MagicMock, patch

from openhands.resolver.interfaces.azure_devops import AzureDevOpsPRHandler


def test_pr_title_escaping():
    """Test that PR titles are properly escaped when creating a pull request."""
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Git client
        mock_git_client = MagicMock()

        # Mock the get_repositories method
        mock_repo = MagicMock()
        mock_repo.id = 'repo-id'
        mock_repo.name = 'test-repo'
        mock_git_client.get_repositories.return_value = [mock_repo]

        # Mock the create_pull_request method
        mock_created_pr = MagicMock()
        mock_created_pr.pull_request_id = 123
        mock_git_client.create_pull_request.return_value = mock_created_pr

        # Set up the connection mock to return the Git client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Create an instance of PRHandler
        handler = AzureDevOpsPRHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test with a title containing special characters
        pr_data = {
            'title': 'Fix bug with "quotes" and \'apostrophes\'',
            'body': 'This PR fixes a bug with special characters.',
            'head': 'feature-branch',
            'base': 'main',
        }

        result = handler.create_pull_request(pr_data)

        # Verify that create_pull_request was called with the correct arguments
        mock_git_client.create_pull_request.assert_called_once()

        # Get the GitPullRequest object that was passed to create_pull_request
        call_args = mock_git_client.create_pull_request.call_args[0]
        pr_arg = call_args[0]

        # Verify that the title was passed correctly
        assert pr_arg.title == 'Fix bug with "quotes" and \'apostrophes\''

        # Verify that the result contains the expected fields
        assert result['id'] == 123
        assert result['number'] == 123
        assert 'html_url' in result
