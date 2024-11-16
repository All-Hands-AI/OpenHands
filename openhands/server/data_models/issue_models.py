from typing import Literal

from pydantic import BaseModel, Field


class ResolveIssueDataModel(BaseModel):
    owner: str = Field(..., description='Github owner of the repo')
    repo: str = Field(..., description='Github repository name')
    token: str = Field(..., description='Github token to access the repository')
    username: str = Field(..., description='Github username to access the repository')
    max_iterations: int = Field(50, description='Maximum number of iterations to run')
    issue_type: Literal['issue', 'pr'] = Field(
        ..., description='Type of issue to resolve (issue or pr)'
    )
    issue_number: int = Field(..., description='Issue number to resolve')
    comment_id: int | None = Field(
        None, description='Optional ID of a specific comment to focus on'
    )
    # PR-related fields
    pr_type: Literal['branch', 'draft', 'ready'] = Field(
        'draft', description='Type of PR to create (branch, draft, ready)'
    )
    fork_owner: str | None = Field(None, description='Optional owner to fork to')
    send_on_failure: bool = Field(
        False, description='Whether to send PR even if resolution failed'
    )


