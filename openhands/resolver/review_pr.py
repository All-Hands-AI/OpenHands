"""Module for reviewing pull requests."""

import argparse
import os
import pathlib

import jinja2
import litellm
import requests

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.issue_definitions import PRHandler


def get_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Get the diff for a pull request."""
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def post_review_comment(
    owner: str, repo: str, pr_number: int, token: str, review: str
) -> None:
    """Post a review comment on a pull request."""
    url = f'https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    data = {'body': review}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()


def review_pr(
    owner: str,
    repo: str,
    token: str,
    username: str,
    output_dir: str,
    llm_config: LLMConfig,
    issue_number: int,
) -> None:
    """Review a pull request.

    Args:
        owner: Github owner of the repo.
        repo: Github repository name.
        token: Github token to access the repository.
        username: Github username to access the repository.
        output_dir: Output directory to write the results.
        llm_config: Configuration for the language model.
        issue_number: PR number to review.
    """
    # Create output directory
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
    pathlib.Path(os.path.join(output_dir, 'infer_logs')).mkdir(
        parents=True, exist_ok=True
    )
    logger.info(f'Using output directory: {output_dir}')

    # Get PR handler
    pr_handler = PRHandler(owner, repo, token)

    # Get PR details
    issues: list[GithubIssue] = pr_handler.get_converted_issues(
        issue_numbers=[issue_number], comment_id=None
    )
    pr = issues[0]

    # Get PR diff
    diff = get_pr_diff(owner, repo, issue_number, token)

    # Load review template
    with open(
        os.path.join(os.path.dirname(__file__), 'prompts/review'),
        'r',
    ) as f:
        template = jinja2.Template(f.read())

    # Generate review instruction
    instruction = template.render(
        body=f'PR #{pr.number}: {pr.title}\n\n{pr.body}\n\nDiff:\n```diff\n{diff}\n```'
    )

    # Get review from LLM
    response = litellm.completion(
        model=llm_config.model,
        messages=[{'role': 'user', 'content': instruction}],
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
    )
    review = response.choices[0].message.content.strip()

    # Post review comment
    post_review_comment(owner, repo, issue_number, token, review)
    logger.info('Posted review comment successfully')


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Review a pull request.')
    parser.add_argument(
        '--repo', type=str, required=True, help='Repository in owner/repo format'
    )
    parser.add_argument(
        '--issue-number', type=int, required=True, help='PR number to review'
    )
    parser.add_argument('--issue-type', type=str, required=True, help='Issue type (pr)')

    args = parser.parse_args()

    # Split repo into owner and name
    owner, repo = args.repo.split('/')

    # Configure LLM
    llm_config = LLMConfig(
        model=os.environ['LLM_MODEL'],
        api_key=os.environ['LLM_API_KEY'],
        base_url=os.environ.get('LLM_BASE_URL'),
    )

    # Review PR
    review_pr(
        owner=owner,
        repo=repo,
        token=os.environ['GITHUB_TOKEN'],
        username=os.environ['GITHUB_USERNAME'],
        output_dir='/tmp/output',
        llm_config=llm_config,
        issue_number=args.issue_number,
    )


if __name__ == '__main__':
    main()
