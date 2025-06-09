from typing import Any

from openhands.resolver.interfaces.issue import (
    Issue,
    IssueHandlerInterface,
    ReviewThread,
)


class BitbucketIssueHandler(IssueHandlerInterface):
    """Stub implementation of BitbucketIssueHandler that implements the IssueHandlerInterface.

    This is a placeholder implementation that satisfies the interface requirements.
    The actual implementation would be more complex and would interact with the Bitbucket API.
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        token: str,
        username: str | None = None,
        base_domain: str = 'bitbucket.org',
    ):
        """Initialize a Bitbucket issue handler.

        Args:
            owner: The owner of the repository
            repo: The name of the repository
            token: The Bitbucket personal access token
            username: Optional Bitbucket username
            base_domain: The domain for Bitbucket Server (default: "bitbucket.org")
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.username = username
        self.base_domain = base_domain

    def set_owner(self, owner: str) -> None:
        self.owner = owner

    def download_issues(self) -> list[Any]:
        return []

    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        return None

    def get_base_url(self) -> str:
        return (
            f'https://api.{self.base_domain}/2.0/repositories/{self.owner}/{self.repo}'
        )

    def get_branch_url(self, branch_name: str) -> str:
        return (
            f'https://{self.base_domain}/{self.owner}/{self.repo}/branch/{branch_name}'
        )

    def get_download_url(self) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.repo}/raw'

    def get_clone_url(self) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.repo}.git'

    def get_pull_url(self, pr_number: int) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.repo}/pull-requests/{pr_number}'

    def get_graphql_url(self) -> str:
        return f'https://api.{self.base_domain}/graphql'

    def get_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
        }

    def get_compare_url(self, branch_name: str) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.repo}/compare/master...{branch_name}'

    def get_branch_name(self, base_branch_name: str) -> str:
        return f'bitbucket-{base_branch_name}'

    def get_default_branch_name(self) -> str:
        return 'master'

    def branch_exists(self, branch_name: str) -> bool:
        return False

    def reply_to_comment(self, pr_number: int, comment_id: str, reply: str) -> None:
        pass

    def send_comment_msg(self, issue_number: int, msg: str) -> None:
        pass

    def get_authorize_url(self) -> str:
        return f'https://{self.base_domain}/site/oauth2/authorize'

    def create_pull_request(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if data is None:
            data = {}
        return {}

    def request_reviewers(self, reviewer: str, pr_number: int) -> None:
        pass

    def get_context_from_external_issues_references(
        self,
        closing_issues: list[str],
        closing_issue_numbers: list[int],
        issue_body: str,
        review_comments: list[str] | None,
        review_threads: list[ReviewThread],
        thread_comments: list[str] | None,
    ) -> list[str]:
        return []

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        return []
