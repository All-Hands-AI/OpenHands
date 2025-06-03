from unittest.mock import MagicMock, patch

from openhands.resolver.interfaces.azure_devops import AzureDevOpsIssueHandler


def test_get_converted_issues():
    """Test getting converted issues from Azure DevOps."""
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the query_by_wiql method
        mock_wiql_result = MagicMock()
        mock_wiql_result.work_items = [MagicMock(id=1), MagicMock(id=2)]
        mock_wit_client.query_by_wiql.return_value = mock_wiql_result

        # Mock the get_work_items method
        mock_work_item1 = MagicMock()
        mock_work_item1.id = 1
        mock_work_item1.fields = {
            'System.Id': 1,
            'System.Title': 'Issue 1',
            'System.Description': 'Description 1',
        }

        mock_work_item2 = MagicMock()
        mock_work_item2.id = 2
        mock_work_item2.fields = {
            'System.Id': 2,
            'System.Title': 'Issue 2',
            'System.Description': 'Description 2',
        }

        mock_wit_client.get_work_items.return_value = [mock_work_item1, mock_work_item2]

        # Mock the get_comments method
        mock_comments = MagicMock()
        mock_comments.comments = []
        mock_wit_client.get_comments.return_value = mock_comments

        # Set up the connection mock to return the WIT client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection.return_value = mock_connection_instance

        # Create an instance of IssueHandler
        handler = AzureDevOpsIssueHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test getting converted issues
        issues = handler.get_converted_issues(issue_numbers=[1, 2])

        # Verify that we got the correct number of issues
        assert len(issues) == 2

        # Verify that the issues have the correct properties
        assert issues[0].number == 1
        assert issues[0].title == 'Issue 1'
        assert issues[0].body == 'Description 1'

        assert issues[1].number == 2
        assert issues[1].title == 'Issue 2'
        assert issues[1].body == 'Description 2'


def test_get_issue_comments():
    """Test getting issue comments from Azure DevOps."""
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the get_comments method
        mock_comment1 = MagicMock()
        mock_comment1.id = 1
        mock_comment1.text = 'Comment 1'

        mock_comment2 = MagicMock()
        mock_comment2.id = 2
        mock_comment2.text = 'Comment 2'

        mock_comments = MagicMock()
        mock_comments.comments = [mock_comment1, mock_comment2]
        mock_wit_client.get_comments.return_value = mock_comments

        # Set up the connection mock to return the WIT client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection.return_value = mock_connection_instance

        # Create an instance of IssueHandler
        handler = AzureDevOpsIssueHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test getting issue comments
        comments = handler.get_issue_comments(1)

        # Verify that we got the correct comments
        assert comments == ['Comment 1', 'Comment 2']


def test_get_default_branch_name():
    """Test getting the default branch name from Azure DevOps."""
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Git client
        mock_git_client = MagicMock()

        # Mock the get_repositories method
        mock_repo = MagicMock()
        mock_repo.name = 'test-repo'
        mock_repo.default_branch = 'refs/heads/main'
        mock_git_client.get_repositories.return_value = [mock_repo]

        # Set up the connection mock to return the Git client
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Create an instance of IssueHandler
        handler = AzureDevOpsIssueHandler(
            'test-org', 'test-project/test-repo', 'test-token'
        )

        # Test getting the default branch name
        branch_name = handler.get_default_branch_name()

        # Verify that we got the correct branch name
        assert branch_name == 'main'
