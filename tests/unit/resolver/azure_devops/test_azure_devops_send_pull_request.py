from unittest.mock import MagicMock, patch

from openhands.resolver.interfaces.azure_devops import AzureDevOpsPRHandler


def test_create_pull_request():
    """Test creating a pull request in Azure DevOps."""
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

        # Test creating a pull request
        pr_data = {
            'title': 'Test PR',
            'body': 'This is a test PR',
            'head': 'feature-branch',
            'base': 'main',
        }

        result = handler.create_pull_request(pr_data)

        # Verify that create_pull_request was called with the correct arguments
        mock_git_client.create_pull_request.assert_called_once()

        # Get the GitPullRequest object that was passed to create_pull_request
        call_args = mock_git_client.create_pull_request.call_args[0]
        pr_arg = call_args[0]
        repo_id = call_args[1]
        project = call_args[2]

        # Verify that the PR was created with the correct parameters
        assert pr_arg.title == 'Test PR'
        assert pr_arg.description == 'This is a test PR'
        assert pr_arg.source_ref_name == 'refs/heads/feature-branch'
        assert pr_arg.target_ref_name == 'refs/heads/main'
        assert repo_id == 'repo-id'
        assert project == 'test-project'

        # Verify that the result contains the expected fields
        assert result['id'] == 123
        assert result['number'] == 123
        assert 'html_url' in result


def test_request_reviewers():
    """Test requesting reviewers for a pull request in Azure DevOps."""
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

        # Mock the create_thread method
        mock_git_client.create_thread.return_value = MagicMock()

        # Set up the connection mock to return the Git client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Create an instance of PRHandler
        handler = AzureDevOpsPRHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test requesting a reviewer
        handler.request_reviewers('test-user', 123)

        # Verify that create_thread was called with the correct arguments
        mock_git_client.create_thread.assert_called_once()

        # Get the arguments that were passed to create_thread
        call_kwargs = mock_git_client.create_thread.call_args[1]

        # Verify that the thread was created with the correct parameters
        assert call_kwargs['repository_id'] == 'repo-id'
        assert call_kwargs['pull_request_id'] == 123
        assert call_kwargs['project'] == 'test-project'
        assert '@test-user' in call_kwargs['comment_thread']['comments'][0]['content']


def test_send_comment_msg():
    """Test sending a comment message to an issue in Azure DevOps."""
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the add_comment method
        mock_wit_client.add_comment.return_value = MagicMock()

        # Set up the connection mock to return the WIT client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection.return_value = mock_connection_instance

        # Create an instance of PRHandler
        handler = AzureDevOpsPRHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test sending a comment message
        handler.send_comment_msg(123, 'This is a test comment')

        # Verify that add_comment was called with the correct arguments
        mock_wit_client.add_comment.assert_called_once_with(
            'test-project', 123, {'text': 'This is a test comment'}
        )
