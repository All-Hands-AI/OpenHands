import tempfile
from unittest.mock import MagicMock, patch

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import ProviderType
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.send_pull_request import make_commit, send_pull_request


@patch("openhands.resolver.send_pull_request.subprocess.run")
def test_commit_message_with_quotes(mock_run):
    # Mock subprocess.run to return appropriate values for different calls
    def side_effect(*args, **kwargs):
        # For git status, return some changes
        if isinstance(args[0], str) and "status --porcelain" in args[0]:
            return MagicMock(returncode=0, stdout="M test.txt", stderr="")
        # For all other calls
        return MagicMock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = side_effect

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test issue with problematic title
        issue = Issue(
            owner="test-owner",
            repo="test-repo",
            number=123,
            title="Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>",
            body="Test body",
            labels=[],
            assignees=[],
            state="open",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            closed_at=None,
            head_branch=None,
            thread_ids=None,
        )

        # Make the commit
        make_commit(temp_dir, issue, "issue")

        # Check that the commit message was correctly formatted
        # Verify that subprocess.run was called with the correct commit message
        expected_message = "Fix issue #123: Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>"

        # Find the call to git commit
        for call in mock_run.call_args_list:
            args = call[0][0] if len(call[0]) > 0 else []
            if (
                isinstance(args, list)
                and len(args) > 2
                and args[0] == "git"
                and "commit" in args
            ):
                commit_message = args[args.index("-m") + 1]
                assert commit_message == expected_message, (
                    f"Expected: {expected_message}, Got: {commit_message}"
                )
                break
        else:
            raise AssertionError("No git commit call found")


@patch("subprocess.run")
def test_pr_title_with_quotes(mock_run, monkeypatch):
    # Mock httpx.post to avoid actual API calls
    class MockResponse:
        def __init__(self, status_code=201):
            self.status_code = status_code
            self.text = ""

        def json(self):
            return {"html_url": "https://github.com/test/test/pull/1"}

        def raise_for_status(self):
            pass

    def mock_post(*args, **kwargs):
        # Verify that the PR title is not over-escaped
        data = kwargs.get("json", {})
        title = data.get("title", "")
        expected = "Fix issue #123: Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>"
        assert title == expected, (
            f"PR title was incorrectly escaped.\nExpected: {expected}\nGot: {title}"
        )
        return MockResponse()

    class MockGetResponse:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.text = ""

        def json(self):
            return {"default_branch": "main"}

        def raise_for_status(self):
            pass

    monkeypatch.setattr("httpx.post", mock_post)
    monkeypatch.setattr("httpx.get", lambda *args, **kwargs: MockGetResponse())
    monkeypatch.setattr(
        "openhands.resolver.interfaces.github.GithubIssueHandler.branch_exists",
        lambda *args, **kwargs: False,
    )

    # Mock subprocess.run to return success
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test issue with problematic title
        logger.info("Creating test issue...")
        issue = Issue(
            owner="test-owner",
            repo="test-repo",
            number=123,
            title="Issue with 'quotes' and \"double quotes\" and <class 'ValueError'>",
            body="Test body",
            labels=[],
            assignees=[],
            state="open",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            closed_at=None,
            head_branch=None,
            thread_ids=None,
        )

        # Try to send a PR - this will fail if the title is incorrectly escaped
        logger.info("Sending PR...")

        send_pull_request(
            issue=issue,
            token="dummy-token",
            username="test-user",
            platform=ProviderType.GITHUB,
            patch_dir=temp_dir,
            pr_type="ready",
        )
