from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.resolver.interfaces.azure_devops import AzureDevOpsPRHandler
from openhands.resolver.interfaces.issue_definitions import ServiceContextPR


def test_pr_handler_get_converted_issues_with_comments():
    # Mock the necessary dependencies
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

        # Mock the get_pull_requests method to return a list of PRs
        mock_pr = MagicMock()
        mock_pr.pull_request_id = 1
        mock_pr.title = 'Test PR'
        mock_pr.description = 'Test Body fixes #1'
        mock_pr.source_ref_name = 'refs/heads/test-branch'
        mock_pr.repository = MagicMock(id='repo-id')
        mock_git_client.get_pull_requests.return_value = [mock_pr]

        # Mock the get_pull_request method
        mock_git_client.get_pull_request.return_value = mock_pr

        # Mock the get_pull_request_work_items method
        mock_work_item = MagicMock()
        mock_work_item.id = 1
        mock_git_client.get_pull_request_work_items.return_value = [mock_work_item]

        # Mock the get_threads method
        mock_thread = MagicMock()
        mock_thread.id = 'thread-1'
        mock_thread.status = 'active'
        mock_thread.is_deleted = False

        mock_comment1 = MagicMock()
        mock_comment1.id = 123
        mock_comment1.content = 'First comment'

        mock_comment2 = MagicMock()
        mock_comment2.id = 456
        mock_comment2.content = 'Second comment'

        mock_thread.comments = [mock_comment1, mock_comment2]

        mock_thread_context = MagicMock()
        mock_thread_context.file_path = 'file1.txt'
        mock_thread.thread_context = mock_thread_context

        mock_git_client.get_threads.return_value = [mock_thread]

        # Mock the Work Item Tracking client
        mock_wit_client = MagicMock()

        # Mock the get_work_items method
        mock_work_item_detail = MagicMock()
        mock_work_item_detail.id = 1
        mock_work_item_detail.fields = {
            'System.Id': 1,
            'System.Title': 'Referenced Issue',
            'System.Description': 'This is additional context from an externally referenced issue.',
        }
        mock_wit_client.get_work_items.return_value = [mock_work_item_detail]

        # Set up the connection mock to return the clients
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection_instance.clients.get_work_item_tracking_client.return_value = (
            mock_wit_client
        )
        mock_connection.return_value = mock_connection_instance

        # Create an instance of PRHandler
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextPR(
            AzureDevOpsPRHandler('test-org', 'test-project/test-repo', 'test-token'),
            llm_config,
        )

        # Get converted issues
        prs = handler.get_converted_issues(issue_numbers=[1])

        # Verify that we got exactly one PR
        assert len(prs) == 1

        # Verify that review_threads are set correctly
        assert len(prs[0].review_threads) == 1
        assert prs[0].review_threads[0].comment == 'First comment\nSecond comment'
        assert prs[0].review_threads[0].files == ['file1.txt']

        # Verify other fields are set correctly
        assert prs[0].number == 1
        assert prs[0].title == 'Test PR'
        assert prs[0].body == 'Test Body fixes #1'
        assert prs[0].owner == 'test-org'
        assert prs[0].repo == 'test-project/test-repo'
        assert prs[0].head_branch == 'test-branch'
        assert prs[0].closing_issues == [
            'This is additional context from an externally referenced issue.'
        ]


def test_pr_handler_get_converted_issues_with_specific_comment_id():
    # Define the specific comment_id to filter
    specific_comment_id = 123

    # Mock the necessary dependencies
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

        # Mock the get_pull_requests method to return a list of PRs
        mock_pr = MagicMock()
        mock_pr.pull_request_id = 1
        mock_pr.title = 'Test PR'
        mock_pr.description = 'Test Body'
        mock_pr.source_ref_name = 'refs/heads/test-branch'
        mock_pr.repository = MagicMock(id='repo-id')
        mock_git_client.get_pull_requests.return_value = [mock_pr]

        # Mock the get_pull_request method
        mock_git_client.get_pull_request.return_value = mock_pr

        # Mock the get_pull_request_work_items method
        mock_git_client.get_pull_request_work_items.return_value = []

        # Mock the get_threads method
        mock_thread = MagicMock()
        mock_thread.id = 'thread-1'
        mock_thread.status = 'active'
        mock_thread.is_deleted = False

        mock_comment1 = MagicMock()
        mock_comment1.id = specific_comment_id
        mock_comment1.content = 'Specific comment'

        mock_comment2 = MagicMock()
        mock_comment2.id = 456
        mock_comment2.content = 'Another comment'

        mock_thread.comments = [mock_comment1, mock_comment2]

        mock_thread_context = MagicMock()
        mock_thread_context.file_path = 'file1.txt'
        mock_thread.thread_context = mock_thread_context

        mock_git_client.get_threads.return_value = [mock_thread]

        # Set up the connection mock to return the clients
        mock_connection_instance = MagicMock()
        mock_connection_instance.clients.get_git_client.return_value = mock_git_client
        mock_connection.return_value = mock_connection_instance

        # Create an instance of PRHandler
        llm_config = LLMConfig(model='test', api_key='test')
        handler = ServiceContextPR(
            AzureDevOpsPRHandler('test-org', 'test-project/test-repo', 'test-token'),
            llm_config,
        )

        # Get converted issues with a specific comment_id
        prs = handler.get_converted_issues(
            issue_numbers=[1], comment_id=specific_comment_id
        )

        # Verify that we got exactly one PR
        assert len(prs) == 1

        # Verify that review_threads contain only the thread with the specific comment
        assert len(prs[0].review_threads) == 1
        assert 'Specific comment' in prs[0].review_threads[0].comment
        assert prs[0].review_threads[0].files == ['file1.txt']

        # Verify other fields are set correctly
        assert prs[0].number == 1
        assert prs[0].title == 'Test PR'
        assert prs[0].body == 'Test Body'
        assert prs[0].owner == 'test-org'
        assert prs[0].repo == 'test-project/test-repo'
        assert prs[0].head_branch == 'test-branch'
