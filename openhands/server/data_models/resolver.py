from typing import Any, Literal

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


class SendPullRequestDataModel(BaseModel):
    issue_number: int = Field(..., description='Issue number to create PR for')
    pr_type: Literal['branch', 'draft', 'ready'] = Field(
        ..., description='Type of PR to create (branch, draft, ready)'
    )
    fork_owner: str | None = Field(None, description='Optional owner to fork to')
    send_on_failure: bool = Field(
        False, description='Whether to send PR even if resolution failed'
    )


async def resolve_github_issue_with_model(
    data: ResolveIssueDataModel,
    llm_config: Any,
    runtime_container_image: str,
    output_dir: str,
) -> dict[str, str]:
    """Resolve a GitHub issue using the provided data model.

    Args:
        data: The issue resolution request data
        llm_config: The LLM configuration to use
        runtime_container_image: The runtime container image to use
        output_dir: The directory to store output files

    Returns:
        A dictionary containing the resolution results
    """
    from openhands.resolver.resolve_issue import resolve_issue

    try:
        await resolve_issue(
            owner=data.owner,
            repo=data.repo,
            token=data.token,
            username=data.username,
            max_iterations=data.max_iterations,
            output_dir=output_dir,
            llm_config=llm_config,
            runtime_container_image=runtime_container_image,
            prompt_template='',  # Using default for now
            issue_type=data.issue_type,
            repo_instruction=None,
            issue_number=data.issue_number,
            comment_id=data.comment_id,
            reset_logger=True,
        )

        # Read output.jsonl file
        import os
        output_file = os.path.join(output_dir, 'output.jsonl')
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                return {'status': 'success', 'output': f.read()}
        else:
            return {'status': 'error', 'message': 'No output file generated'}

    except Exception as e:
        return {'status': 'error', 'message': str(e)}


async def send_pull_request_with_model(
    data: SendPullRequestDataModel,
    llm_config: Any,
    output_dir: str,
    github_token: str,
    github_username: str | None = None,
) -> dict[str, str | dict[str, Any]]:
    """Create a pull request using the provided data model.

    Args:
        data: The PR creation request data
        llm_config: The LLM configuration to use
        output_dir: The directory containing resolver output
        github_token: The GitHub token to use
        github_username: Optional GitHub username

    Returns:
        A dictionary containing the PR creation results
    """
    from openhands.resolver.io_utils import load_single_resolver_output
    from openhands.resolver.send_pull_request import process_single_issue

    try:
        resolver_output = load_single_resolver_output(output_dir, data.issue_number)
        if not resolver_output:
            raise ValueError(f'No resolver output found for issue {data.issue_number}')

        result = process_single_issue(
            output_dir=output_dir,
            resolver_output=resolver_output,
            github_token=github_token,
            github_username=github_username,
            pr_type=data.pr_type,
            llm_config=llm_config,
            fork_owner=data.fork_owner,
            send_on_failure=data.send_on_failure,
        )
        if result.success:
            return {'status': 'success', 'result': {'url': result.url}}
        else:
            return {'status': 'error', 'message': result.error or 'Unknown error'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}