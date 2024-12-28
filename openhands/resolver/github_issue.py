from typing import Optional

from pydantic import BaseModel


class ReviewThread(BaseModel):
    comment: str
    files: list[str]


class GithubIssue(BaseModel):
    owner: str
    repo: str
    number: int
    title: str
    body: str
    thread_comments: Optional[list[str]] = None  # Added field for issue thread comments
    closing_issues: Optional[list[str]] = None
    review_comments: Optional[list[str]] = None
    review_threads: Optional[list[ReviewThread]] = None
    thread_ids: Optional[list[str]] = None
    head_branch: Optional[str] = None
    has_merge_conflicts: Optional[bool] = None
    failed_checks: Optional[list[dict[str, Optional[str]]]] = None
