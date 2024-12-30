import argparse
import json
import os
import shutil
import subprocess

import jinja2
import requests

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.io_utils import (
    load_all_resolver_outputs,
    load_single_resolver_output,
)
from openhands.resolver.patching import apply_diff, parse_patch
from openhands.resolver.resolver_output import ResolverOutput


def apply_patch(repo_dir: str, patch: str) -> None:
    """Apply a patch to a repository.

    Args:
        repo_dir: The directory containing the repository
        patch: The patch to apply
    """
    diffs = parse_patch(patch)
    for diff in diffs:
        if not diff.header.new_path:
            print('Warning: Could not determine file to patch')
            continue

        # Remove both "a/" and "b/" prefixes from paths
        old_path = (
            os.path.join(
                repo_dir, diff.header.old_path.removeprefix('a/').removeprefix('b/')
            )
            if diff.header.old_path and diff.header.old_path != '/dev/null'
            else None
        )
        new_path = os.path.join(
            repo_dir, diff.header.new_path.removeprefix('a/').removeprefix('b/')
        )

        # Check if the file is being deleted
        if diff.header.new_path == '/dev/null':
            assert old_path is not None
            if os.path.exists(old_path):
                os.remove(old_path)
                print(f'Deleted file: {old_path}')
            continue

        # Handle file rename
        if old_path and new_path and 'rename from' in patch:
            # Create parent directory of new path
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            try:
                # Try to move the file directly
                shutil.move(old_path, new_path)
            except shutil.SameFileError:
                # If it's the same file (can happen with directory renames), copy first then remove
                shutil.copy2(old_path, new_path)
                os.remove(old_path)

            # Try to remove empty parent directories
            old_dir = os.path.dirname(old_path)
            while old_dir and old_dir.startswith(repo_dir):
                try:
                    os.rmdir(old_dir)
                    old_dir = os.path.dirname(old_dir)
                except OSError:
                    # Directory not empty or other error, stop trying to remove parents
                    break
            continue

        if old_path:
            # Open the file in binary mode to detect line endings
            with open(old_path, 'rb') as f:
                original_content = f.read()

            # Detect line endings
            if b'\r\n' in original_content:
                newline = '\r\n'
            elif b'\n' in original_content:
                newline = '\n'
            else:
                newline = None  # Let Python decide

            try:
                with open(old_path, 'r', newline=newline) as f:
                    split_content = [x.strip(newline) for x in f.readlines()]
            except UnicodeDecodeError as e:
                logger.error(f'Error reading file {old_path}: {e}')
                split_content = []
        else:
            newline = '\n'
            split_content = []

        if diff.changes is None:
            print(f'Warning: No changes to apply for {old_path}')
            continue

        new_content = apply_diff(diff, split_content)

        # Ensure the directory exists before writing the file
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        # Write the new content using the detected line endings
        with open(new_path, 'w', newline=newline) as f:
            for line in new_content:
                print(line, file=f)

    print('Patch applied successfully')


def initialize_repo(
    output_dir: str, issue_number: int, issue_type: str, base_commit: str | None = None
) -> str:
    """Initialize the repository.

    Args:
        output_dir: The output directory to write the repository to
        issue_number: The issue number to fix
        issue_type: The type of the issue
        base_commit: The base commit to checkout (if issue_type is pr)
    """
    src_dir = os.path.join(output_dir, 'repo')
    dest_dir = os.path.join(output_dir, 'patches', f'{issue_type}_{issue_number}')

    if not os.path.exists(src_dir):
        raise ValueError(f'Source directory {src_dir} does not exist.')

    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)

    shutil.copytree(src_dir, dest_dir)
    print(f'Copied repository to {dest_dir}')

    # Checkout the base commit if provided
    if base_commit:
        result = subprocess.run(
            f'git -C {dest_dir} checkout {base_commit}',
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f'Error checking out commit: {result.stderr}')
            raise RuntimeError('Failed to check out commit')

    return dest_dir


def make_commit(repo_dir: str, issue: GithubIssue, issue_type: str) -> None:
    """Make a commit with the changes to the repository.

    Args:
        repo_dir: The directory containing the repository
        issue: The issue to fix
        issue_type: The type of the issue
    """
    # Check if git username is set
    result = subprocess.run(
        f'git -C {repo_dir} config user.name',
        shell=True,
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        # If username is not set, configure git
        subprocess.run(
            f'git -C {repo_dir} config user.name "openhands" && '
            f'git -C {repo_dir} config user.email "openhands@all-hands.dev" && '
            f'git -C {repo_dir} config alias.git "git --no-pager"',
            shell=True,
            check=True,
        )
        print('Git user configured as openhands')

    # Add all changes to the git index
    result = subprocess.run(
        f'git -C {repo_dir} add .', shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'Error adding files: {result.stderr}')
        raise RuntimeError('Failed to add files to git')

    # Check the status of the git index
    status_result = subprocess.run(
        f'git -C {repo_dir} status --porcelain',
        shell=True,
        capture_output=True,
        text=True,
    )

    # If there are no changes, raise an error
    if not status_result.stdout.strip():
        print(f'No changes to commit for issue #{issue.number}. Skipping commit.')
        raise RuntimeError('ERROR: Openhands failed to make code changes.')

    # Prepare the commit message
    commit_message = f'Fix {issue_type} #{issue.number}: {issue.title}'

    # Commit the changes
    result = subprocess.run(
        ['git', '-C', repo_dir, 'commit', '-m', commit_message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'Failed to commit changes: {result}')


def branch_exists(base_url: str, branch_name: str, headers: dict) -> bool:
    """Check if a branch exists in the GitHub repository.

    Args:
        base_url: The base URL of the GitHub repository API
        branch_name: The name of the branch to check
        headers: The HTTP headers to use for authentication
    """
    print(f'Checking if branch {branch_name} exists...')
    response = requests.get(f'{base_url}/branches/{branch_name}', headers=headers)
    exists = response.status_code == 200
    print(f'Branch {branch_name} exists: {exists}')
    return exists


def send_pull_request(
    github_issue: GithubIssue,
    github_token: str,
    github_username: str | None,
    patch_dir: str,
    pr_type: str,
    fork_owner: str | None = None,
    additional_message: str | None = None,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
) -> str:
    """Send a pull request to a GitHub repository.

    Args:
        github_issue: The issue to send the pull request for
        github_token: The GitHub token to use for authentication
        github_username: The GitHub username, if provided
        patch_dir: The directory containing the patches to apply
        pr_type: The type: branch (no PR created), draft or ready (regular PR created)
        fork_owner: The owner of the fork to push changes to (if different from the original repo owner)
        additional_message: The additional messages to post as a comment on the PR in json list format
        target_branch: The target branch to create the pull request against (defaults to repository default branch)
        reviewer: The GitHub username of the reviewer to assign
        pr_title: Custom title for the pull request (optional)
    """
    if pr_type not in ['branch', 'draft', 'ready']:
        raise ValueError(f'Invalid pr_type: {pr_type}')

    # Set up headers and base URL for GitHub API
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    base_url = f'https://api.github.com/repos/{github_issue.owner}/{github_issue.repo}'

    # Create a new branch with a unique name
    base_branch_name = f'openhands-fix-issue-{github_issue.number}'
    branch_name = base_branch_name
    attempt = 1

    # Find a unique branch name
    print('Checking if branch exists...')
    while branch_exists(base_url, branch_name, headers):
        attempt += 1
        branch_name = f'{base_branch_name}-try{attempt}'

    # Get the default branch or use specified target branch
    print('Getting base branch...')
    if target_branch:
        base_branch = target_branch
        # Verify the target branch exists
        response = requests.get(f'{base_url}/branches/{target_branch}', headers=headers)
        if response.status_code != 200:
            raise ValueError(f'Target branch {target_branch} does not exist')
    else:
        response = requests.get(f'{base_url}', headers=headers)
        response.raise_for_status()
        base_branch = response.json()['default_branch']
    print(f'Base branch: {base_branch}')

    # Create and checkout the new branch
    print('Creating new branch...')
    result = subprocess.run(
        ['git', '-C', patch_dir, 'checkout', '-b', branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f'Error creating new branch: {result.stderr}')
        raise RuntimeError(
            f'Failed to create a new branch {branch_name} in {patch_dir}:'
        )

    # Determine the repository to push to (original or fork)
    push_owner = fork_owner if fork_owner else github_issue.owner
    push_repo = github_issue.repo

    print('Pushing changes...')
    username_and_token = (
        f'{github_username}:{github_token}'
        if github_username
        else f'x-auth-token:{github_token}'
    )
    push_url = f'https://{username_and_token}@github.com/{push_owner}/{push_repo}.git'
    result = subprocess.run(
        ['git', '-C', patch_dir, 'push', push_url, branch_name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f'Error pushing changes: {result.stderr}')
        raise RuntimeError('Failed to push changes to the remote repository')

    # Prepare the PR data: title and body
    final_pr_title = (
        pr_title
        if pr_title
        else f'Fix issue #{github_issue.number}: {github_issue.title}'
    )
    pr_body = f'This pull request fixes #{github_issue.number}.'
    if additional_message:
        pr_body += f'\n\n{additional_message}'
    pr_body += '\n\nAutomatic fix generated by [OpenHands](https://github.com/All-Hands-AI/OpenHands/) 🙌'

    # If we are not sending a PR, we can finish early and return the
    # URL for the user to open a PR manually
    if pr_type == 'branch':
        url = f'https://github.com/{push_owner}/{github_issue.repo}/compare/{branch_name}?expand=1'
    else:
        # Prepare the PR for the GitHub API
        data = {
            'title': final_pr_title,  # No need to escape title for GitHub API
            'body': pr_body,
            'head': branch_name,
            'base': base_branch,
            'draft': pr_type == 'draft',
        }

        # Send the PR and get its URL to tell the user
        response = requests.post(f'{base_url}/pulls', headers=headers, json=data)
        if response.status_code == 403:
            raise RuntimeError(
                'Failed to create pull request due to missing permissions. '
                'Make sure that the provided token has push permissions for the repository.'
            )
        response.raise_for_status()
        pr_data = response.json()

        # Request review if a reviewer was specified
        if reviewer and pr_type != 'branch':
            review_data = {'reviewers': [reviewer]}
            review_response = requests.post(
                f'{base_url}/pulls/{pr_data["number"]}/requested_reviewers',
                headers=headers,
                json=review_data,
            )
            if review_response.status_code != 201:
                print(
                    f'Warning: Failed to request review from {reviewer}: {review_response.text}'
                )

        url = pr_data['html_url']

    print(
        f'{pr_type} created: {url}\n\n--- Title: {final_pr_title}\n\n--- Body:\n{pr_body}'
    )

    return url


def reply_to_comment(github_token: str, comment_id: str, reply: str):
    """Reply to a comment on a GitHub issue or pull request.

    Args:
        github_token: The GitHub token to use for authentication
        comment_id: The ID of the comment to reply to
        reply: The reply message to post
    """
    # Opting for graphql as REST API doesn't allow reply to replies in comment threads
    query = """
            mutation($body: String!, $pullRequestReviewThreadId: ID!) {
                addPullRequestReviewThreadReply(input: { body: $body, pullRequestReviewThreadId: $pullRequestReviewThreadId }) {
                    comment {
                        id
                        body
                        createdAt
                    }
                }
            }
            """

    # Prepare the reply to the comment
    comment_reply = f'Openhands fix success summary\n\n\n{reply}'
    variables = {'body': comment_reply, 'pullRequestReviewThreadId': comment_id}
    url = 'https://api.github.com/graphql'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Content-Type': 'application/json',
    }

    # Send the reply to the comment
    response = requests.post(
        url, json={'query': query, 'variables': variables}, headers=headers
    )
    response.raise_for_status()


def send_comment_msg(base_url: str, issue_number: int, github_token: str, msg: str):
    """Send a comment message to a GitHub issue or pull request.

    Args:
        base_url: The base URL of the GitHub repository API
        issue_number: The issue or pull request number
        github_token: The GitHub token to use for authentication
        msg: The message content to post as a comment
    """
    # Set up headers for GitHub API
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Post a comment on the PR
    comment_url = f'{base_url}/issues/{issue_number}/comments'
    comment_data = {'body': msg}
    comment_response = requests.post(comment_url, headers=headers, json=comment_data)
    if comment_response.status_code != 201:
        print(
            f'Failed to post comment: {comment_response.status_code} {comment_response.text}'
        )
    else:
        print(f'Comment added to the PR: {msg}')


def update_existing_pull_request(
    github_issue: GithubIssue,
    github_token: str,
    github_username: str | None,
    patch_dir: str,
    llm_config: LLMConfig,
    comment_message: str | None = None,
    additional_message: str | None = None,
) -> str:
    """Update an existing pull request with the new patches.

    Args:
        github_issue: The issue to update.
        github_token: The GitHub token to use for authentication.
        github_username: The GitHub username to use for authentication.
        patch_dir: The directory containing the patches to apply.
        llm_config: The LLM configuration to use for summarizing changes.
        comment_message: The main message to post as a comment on the PR.
        additional_message: The additional messages to post as a comment on the PR in json list format.
    """
    # Set up base URL for GitHub API
    base_url = f'https://api.github.com/repos/{github_issue.owner}/{github_issue.repo}'
    branch_name = github_issue.head_branch

    # Prepare the push command
    push_command = (
        f'git -C {patch_dir} push '
        f'https://{github_username}:{github_token}@github.com/'
        f'{github_issue.owner}/{github_issue.repo}.git {branch_name}'
    )

    # Push the changes to the existing branch
    result = subprocess.run(push_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'Error pushing changes: {result.stderr}')
        raise RuntimeError('Failed to push changes to the remote repository')

    pr_url = f'https://github.com/{github_issue.owner}/{github_issue.repo}/pull/{github_issue.number}'
    print(f'Updated pull request {pr_url} with new patches.')

    # Generate a summary of all comment success indicators for PR message
    if not comment_message and additional_message:
        try:
            explanations = json.loads(additional_message)
            if explanations:
                comment_message = (
                    'OpenHands made the following changes to resolve the issues:\n\n'
                )
                for explanation in explanations:
                    comment_message += f'- {explanation}\n'

                # Summarize with LLM if provided
                if llm_config is not None:
                    llm = LLM(llm_config)
                    with open(
                        os.path.join(
                            os.path.dirname(__file__),
                            'prompts/resolve/pr-changes-summary.jinja',
                        ),
                        'r',
                    ) as f:
                        template = jinja2.Template(f.read())
                    prompt = template.render(comment_message=comment_message)
                    response = llm.completion(
                        messages=[{'role': 'user', 'content': prompt}],
                    )
                    comment_message = response.choices[0].message.content.strip()

        except (json.JSONDecodeError, TypeError):
            comment_message = f'A new OpenHands update is available, but failed to parse or summarize the changes:\n{additional_message}'

    # Post a comment on the PR
    if comment_message:
        send_comment_msg(base_url, github_issue.number, github_token, comment_message)

    # Reply to each unresolved comment thread
    if additional_message and github_issue.thread_ids:
        try:
            explanations = json.loads(additional_message)
            for count, reply_comment in enumerate(explanations):
                comment_id = github_issue.thread_ids[count]
                reply_to_comment(github_token, comment_id, reply_comment)
        except (json.JSONDecodeError, TypeError):
            msg = f'Error occured when replying to threads; success explanations {additional_message}'
            send_comment_msg(base_url, github_issue.number, github_token, msg)

    return pr_url


def process_single_issue(
    output_dir: str,
    resolver_output: ResolverOutput,
    github_token: str,
    github_username: str,
    pr_type: str,
    llm_config: LLMConfig,
    fork_owner: str | None,
    send_on_failure: bool,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
) -> None:
    if not resolver_output.success and not send_on_failure:
        print(
            f'Issue {resolver_output.issue.number} was not successfully resolved. Skipping PR creation.'
        )
        return

    issue_type = resolver_output.issue_type

    if issue_type == 'issue':
        patched_repo_dir = initialize_repo(
            output_dir,
            resolver_output.issue.number,
            issue_type,
            resolver_output.base_commit,
        )
    elif issue_type == 'pr':
        patched_repo_dir = initialize_repo(
            output_dir,
            resolver_output.issue.number,
            issue_type,
            resolver_output.issue.head_branch,
        )
    else:
        raise ValueError(f'Invalid issue type: {issue_type}')

    apply_patch(patched_repo_dir, resolver_output.git_patch)

    make_commit(patched_repo_dir, resolver_output.issue, issue_type)

    if issue_type == 'pr':
        update_existing_pull_request(
            github_issue=resolver_output.issue,
            github_token=github_token,
            github_username=github_username,
            patch_dir=patched_repo_dir,
            additional_message=resolver_output.result_explanation,
            llm_config=llm_config,
        )
    else:
        send_pull_request(
            github_issue=resolver_output.issue,
            github_token=github_token,
            github_username=github_username,
            patch_dir=patched_repo_dir,
            pr_type=pr_type,
            fork_owner=fork_owner,
            additional_message=resolver_output.result_explanation,
            target_branch=target_branch,
            reviewer=reviewer,
            pr_title=pr_title,
        )


def process_all_successful_issues(
    output_dir: str,
    github_token: str,
    github_username: str,
    pr_type: str,
    llm_config: LLMConfig,
    fork_owner: str | None,
) -> None:
    output_path = os.path.join(output_dir, 'output.jsonl')
    for resolver_output in load_all_resolver_outputs(output_path):
        if resolver_output.success:
            print(f'Processing issue {resolver_output.issue.number}')
            process_single_issue(
                output_dir,
                resolver_output,
                github_token,
                github_username,
                pr_type,
                llm_config,
                fork_owner,
                False,
                None,
            )


def main():
    parser = argparse.ArgumentParser(description='Send a pull request to Github.')
    parser.add_argument(
        '--github-token',
        type=str,
        default=None,
        help='Github token to access the repository.',
    )
    parser.add_argument(
        '--github-username',
        type=str,
        default=None,
        help='Github username to access the repository.',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Output directory to write the results.',
    )
    parser.add_argument(
        '--pr-type',
        type=str,
        default='draft',
        choices=['branch', 'draft', 'ready'],
        help='Type of the pull request to send [branch, draft, ready]',
    )
    parser.add_argument(
        '--issue-number',
        type=str,
        required=True,
        help="Issue number to send the pull request for, or 'all_successful' to process all successful issues.",
    )
    parser.add_argument(
        '--fork-owner',
        type=str,
        default=None,
        help='Owner of the fork to push changes to (if different from the original repo owner).',
    )
    parser.add_argument(
        '--send-on-failure',
        action='store_true',
        help='Send a pull request even if the issue was not successfully resolved.',
    )
    parser.add_argument(
        '--llm-model',
        type=str,
        default=None,
        help='LLM model to use for summarizing changes.',
    )
    parser.add_argument(
        '--llm-api-key',
        type=str,
        default=None,
        help='API key for the LLM model.',
    )
    parser.add_argument(
        '--llm-base-url',
        type=str,
        default=None,
        help='Base URL for the LLM model.',
    )
    parser.add_argument(
        '--target-branch',
        type=str,
        default=None,
        help='Target branch to create the pull request against (defaults to repository default branch)',
    )
    parser.add_argument(
        '--reviewer',
        type=str,
        help='GitHub username of the person to request review from',
        default=None,
    )
    parser.add_argument(
        '--pr-title',
        type=str,
        help='Custom title for the pull request',
        default=None,
    )
    my_args = parser.parse_args()

    github_token = (
        my_args.github_token if my_args.github_token else os.getenv('GITHUB_TOKEN')
    )
    if not github_token:
        raise ValueError(
            'Github token is not set, set via --github-token or GITHUB_TOKEN environment variable.'
        )
    github_username = (
        my_args.github_username
        if my_args.github_username
        else os.getenv('GITHUB_USERNAME')
    )

    llm_config = LLMConfig(
        model=my_args.llm_model or os.environ['LLM_MODEL'],
        api_key=my_args.llm_api_key or os.environ['LLM_API_KEY'],
        base_url=my_args.llm_base_url or os.environ.get('LLM_BASE_URL', None),
    )

    if not os.path.exists(my_args.output_dir):
        raise ValueError(f'Output directory {my_args.output_dir} does not exist.')

    if my_args.issue_number == 'all_successful':
        if not github_username:
            raise ValueError('Github username is required.')
        process_all_successful_issues(
            my_args.output_dir,
            github_token,
            github_username,
            my_args.pr_type,
            llm_config,
            my_args.fork_owner,
        )
    else:
        if not my_args.issue_number.isdigit():
            raise ValueError(f'Issue number {my_args.issue_number} is not a number.')
        issue_number = int(my_args.issue_number)
        output_path = os.path.join(my_args.output_dir, 'output.jsonl')
        resolver_output = load_single_resolver_output(output_path, issue_number)
        if not github_username:
            raise ValueError('Github username is required.')
        process_single_issue(
            my_args.output_dir,
            resolver_output,
            github_token,
            github_username,
            my_args.pr_type,
            llm_config,
            my_args.fork_owner,
            my_args.send_on_failure,
            my_args.target_branch,
            my_args.reviewer,
            my_args.pr_title,
        )


if __name__ == '__main__':
    main()
