from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.resolver.interfaces.azure_devops import (
    AzureDevOpsIssueHandler,
)
from openhands.resolver.interfaces.issue_definitions import (
    ServiceContextIssue,
)


def test_get_converted_issues_initializes_review_comments():
    # Mock the necessary dependencies
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the query_by_wiql method
        mock_wiql_result = MagicMock()
        mock_wiql_result.work_items = [MagicMock(id=1)]
        mock_wit_client.query_by_wiql.return_value = mock_wiql_result

        # Mock the get_work_items method
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            'System.Id': 1,
            'System.Title': 'Test Issue',
            'System.Description': 'Test Body',
        }
        mock_wit_client.get_work_items.return_value = [mock_work_item]

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
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextIssue(
            AzureDevOpsIssueHandler('test-org', 'test-project/test-repo', 'test-token'),
            llm_config,
        )

        # Get converted issues
        issues = handler.get_converted_issues(issue_numbers=[1])

        # Verify that we got exactly one issue
        assert len(issues) == 1

        # Verify that review_comments is initialized as None
        assert issues[0].review_comments is None

        # Verify other fields are set correctly
        assert issues[0].number == 1
        assert issues[0].title == 'Test Issue'
        assert issues[0].body == 'Test Body'
        assert issues[0].owner == 'test-org'
        assert issues[0].repo == 'test-project/test-repo'


def test_get_converted_issues_handles_empty_body():
    # Mock the necessary dependencies
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the query_by_wiql method
        mock_wiql_result = MagicMock()
        mock_wiql_result.work_items = [MagicMock(id=1)]
        mock_wit_client.query_by_wiql.return_value = mock_wiql_result

        # Mock the get_work_items method
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_work_item.fields = {
            'System.Id': 1,
            'System.Title': 'Test Issue',
            'System.Description': None,
        }
        mock_wit_client.get_work_items.return_value = [mock_work_item]

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
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextIssue(
            AzureDevOpsIssueHandler('test-org', 'test-project/test-repo', 'test-token'),
            llm_config,
        )

        # Get converted issues
        issues = handler.get_converted_issues(issue_numbers=[1])

        # Verify that we got exactly one issue
        assert len(issues) == 1

        # Verify that body is empty string when None
        assert issues[0].body == ''

        # Verify other fields are set correctly
        assert issues[0].number == 1
        assert issues[0].title == 'Test Issue'
        assert issues[0].owner == 'test-org'
        assert issues[0].repo == 'test-project/test-repo'

        # Verify that review_comments is initialized as None
        assert issues[0].review_comments is None


def test_get_issue_comments_with_specific_comment_id():
    # Mock the necessary dependencies
    with patch(
        'openhands.resolver.interfaces.azure_devops.Connection'
    ) as mock_connection:
        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the get_comments method
        mock_comment1 = MagicMock()
        mock_comment1.id = 123
        mock_comment1.text = 'First comment'

        mock_comment2 = MagicMock()
        mock_comment2.id = 456
        mock_comment2.text = 'Second comment'

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
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextIssue(
            AzureDevOpsIssueHandler('test-org', 'test-project/test-repo', 'test-token'),
            llm_config,
        )

        # Get comments with a specific comment_id
        specific_comment = handler.get_issue_comments(issue_number=1, comment_id=123)

        # Verify only the specific comment is returned
        assert specific_comment == ['First comment']
