from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ReviewThread(BaseModel):
    comment: str
    files: list[str]


class Issue(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    body: str
    thread_comments: list[str] | None = None  # Added field for issue thread comments
    closing_issues: list[str] | None = None
    review_comments: list[str] | None = None
    review_threads: list[ReviewThread] | None = None
    thread_ids: list[str] | None = None
    head_branch: str | None = None
    base_branch: str | None = None


class IssueHandlerInterface(ABC):
    @abstractmethod
    def download_issues(self) -> list[Any]:
        pass

    @abstractmethod
    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        pass

    @abstractmethod
    def get_base_url(self):
        pass

    @abstractmethod
    def get_branch_url(self, branch_name):
        pass

    @abstractmethod
    def get_download_url(self):
        pass

    @abstractmethod
    def get_clone_url(self):
        pass

    @abstractmethod
    def get_graphql_url(self):
        pass

    @abstractmethod
    def get_headers(self):
        pass

    @abstractmethod
    def get_compare_url(self, branch_name):
        pass

    @abstractmethod
    def get_branch_name(self, base_branch_name: str):
        pass

    @abstractmethod
    def branch_exists(self, branch_name: str) -> bool:
        pass

    @abstractmethod
    def reply_to_comment(self, pr_number: int, comment_id: str, reply: str):
        pass

    @abstractmethod
    def send_comment_msg(self, issue_number: int, msg: str):
        pass

    @abstractmethod
    def get_authorize_url(self):
        pass

    @abstractmethod
    def create_pull_request(self, data=dict) -> dict:
        pass

    @abstractmethod
    def request_reviewers(self, reviewer: str, pr_number: int):
        pass

    @abstractmethod
    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Gitlab."""
        pass
