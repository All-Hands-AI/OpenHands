import argparse
import json
import os
import shutil
import subprocess

import jinja2
from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.resolver.interfaces.github import GithubIssueHandler
from openhands.resolver.interfaces.gitlab import GitlabIssueHandler
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.interfaces.issue_definitions import ServiceContextIssue
from openhands.resolver.io_utils import (
    load_all_resolver_outputs,
    load_single_resolver_output,
)
from openhands.resolver.patching import apply_diff, parse_patch
from openhands.resolver.resolver_output import ResolverOutput
from openhands.resolver.utils import (
    Platform,
    identify_token,
)


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


def make_commit(repo_dir: str, issue: Issue, issue_type: str) -> None:
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


def send_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: Platform,
    patch_dir: str,
    pr_type: str,
    fork_owner: str | None = None,
    additional_message: str | None = None,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
) -> str:
    """Send a pull request to a GitHub or Gitlab repository.

    Args:
        issue: The issue to send the pull request for
        token: The GitHub or Gitlab token to use for authentication
        username: The GitHub or Gitlab username, if provided
        platform: The platform of the repository.
        patch_dir: The directory containing the patches to apply
        pr_type: The type: branch (no PR created), draft or ready (regular PR created)
        fork_owner: The owner of the fork to push changes to (if different from the original repo owner)
        additional_message: The additional messages to post as a comment on the PR in json list format
        target_branch: The target branch to create the pull request against (defaults to repository default branch)
        reviewer: The GitHub or Gitlab username of the reviewer to assign
        pr_title: Custom title for the pull request (optional)
    """
    if pr_type not in ['branch', 'draft', 'ready']:
        raise ValueError(f'Invalid pr_type: {pr_type}')

    handler = None
    if platform == Platform.GITHUB:
        handler = ServiceContextIssue(
            GithubIssueHandler(issue.owner, issue.repo, token, username), None
        )
    else:  # platform == Platform.GITLAB
        handler = ServiceContextIssue(
            GitlabIssueHandler(issue.owner, issue.repo, token, username), None
        )

    # Create a new branch with a unique name
    base_branch_name = f'openhands-fix-issue-{issue.number}'
    branch_name = handler.get_branch_name(
        base_branch_name=base_branch_name,
    )

    # Get the default branch or use specified target branch
    print('Getting base branch...')
    if target_branch:
        base_branch = target_branch
        exists = handler.branch_exists(branch_name=target_branch)
        if not exists:
            raise ValueError(f'Target branch {target_branch} does not exist')
    else:
        base_branch = handler.get_default_branch_name()
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
    push_owner = fork_owner if fork_owner else issue.owner

    handler._strategy.set_owner(push_owner)

    print('Pushing changes...')
    push_url = handler.get_clone_url()
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
        pr_title if pr_title else f'Fix issue #{issue.number}: {issue.title}'
    )
    pr_body = f'This pull request fixes #{issue.number}.'
    if additional_message:
        pr_body += f'\n\n{additional_message}'
    pr_body += '\n\nAutomatic fix generated by [OpenHands](https://github.com/All-Hands-AI/OpenHands/) 🙌'

    # If we are not sending a PR, we can finish early and return the
    # URL for the user to open a PR manually
    if pr_type == 'branch':
        url = handler.get_compare_url(branch_name)
    else:
        # Prepare the PR for the GitHub API
        data = {
            'title': final_pr_title,
            ('body' if platform == Platform.GITHUB else 'description'): pr_body,
            ('head' if platform == Platform.GITHUB else 'source_branch'): branch_name,
            ('base' if platform == Platform.GITHUB else 'target_branch'): base_branch,
            'draft': pr_type == 'draft',
        }

        pr_data = handler.create_pull_request(data)
        url = pr_data['html_url']

        print(pr_data)
        # Request review if a reviewer was specified
        if reviewer and pr_type != 'branch':
            number = pr_data['number']
            handler.request_reviewers(reviewer, number)

    print(
        f'{pr_type} created: {url}\n\n--- Title: {final_pr_title}\n\n--- Body:\n{pr_body}'
    )

    return url


def update_existing_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: Platform,
    patch_dir: str,
    llm_config: LLMConfig,
    comment_message: str | None = None,
    additional_message: str | None = None,
) -> str:
    """Update an existing pull request with the new patches.

    Args:
        issue: The issue to update.
        token: The  token to use for authentication.
        username: The username to use for authentication.
        platform: The platform of the repository.
        patch_dir: The directory containing the patches to apply.
        llm_config: The LLM configuration to use for summarizing changes.
        comment_message: The main message to post as a comment on the PR.
        additional_message: The additional messages to post as a comment on the PR in json list format.
    """
    # Set up headers and base URL for GitHub or GitLab API

    handler = None
    if platform == Platform.GITHUB:
        handler = ServiceContextIssue(
            GithubIssueHandler(issue.owner, issue.repo, token, username), llm_config
        )
    else:  # platform == Platform.GITLAB
        handler = ServiceContextIssue(
            GitlabIssueHandler(issue.owner, issue.repo, token, username), llm_config
        )

    branch_name = issue.head_branch

    # Prepare the push command
    push_command = (
        f'git -C {patch_dir} push '
        f'{handler.get_authorize_url()}'
        f'{issue.owner}/{issue.repo}.git {branch_name}'
    )

    # Push the changes to the existing branch
    result = subprocess.run(push_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'Error pushing changes: {result.stderr}')
        raise RuntimeError('Failed to push changes to the remote repository')

    pr_url = handler.get_pull_url(issue.number)
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
        handler.send_comment_msg(issue.number, comment_message)

    # Reply to each unresolved comment thread
    if additional_message and issue.thread_ids:
        try:
            explanations = json.loads(additional_message)
            for count, reply_comment in enumerate(explanations):
                comment_id = issue.thread_ids[count]
                handler.reply_to_comment(issue.number, comment_id, reply_comment)
        except (json.JSONDecodeError, TypeError):
            msg = f'Error occured when replying to threads; success explanations {additional_message}'
            handler.send_comment_msg(issue.number, msg)

    return pr_url


def process_single_issue(
    output_dir: str,
    resolver_output: ResolverOutput,
    token: str,
    username: str,
    platform: Platform,
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
            issue=resolver_output.issue,
            token=token,
            username=username,
            platform=platform,
            patch_dir=patched_repo_dir,
            additional_message=resolver_output.result_explanation,
            llm_config=llm_config,
        )
    else:
        send_pull_request(
            issue=resolver_output.issue,
            token=token,
            username=username,
            platform=platform,
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
    token: str,
    username: str,
    platform: Platform,
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
                token,
                username,
                platform,
                pr_type,
                llm_config,
                fork_owner,
                False,
                None,
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Send a pull request to Github or Gitlab.'
    )
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='token to access the repository.',
    )
    parser.add_argument(
        '--username',
        type=str,
        default=None,
        help='username to access the repository.',
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
        help='GitHub or GitLab username of the person to request review from',
        default=None,
    )
    parser.add_argument(
        '--pr-title',
        type=str,
        help='Custom title for the pull request',
        default=None,
    )
    my_args = parser.parse_args()

    token = my_args.token or os.getenv('GITHUB_TOKEN') or os.getenv('GITLAB_TOKEN')
    if not token:
        raise ValueError(
            'token is not set, set via --token or GITHUB_TOKEN or GITLAB_TOKEN environment variable.'
        )
    username = my_args.username if my_args.username else os.getenv('GIT_USERNAME')

    platform = identify_token(token)
    if platform == Platform.INVALID:
        raise ValueError('Token is invalid.')

    api_key = my_args.llm_api_key or os.environ['LLM_API_KEY']
    llm_config = LLMConfig(
        model=my_args.llm_model or os.environ['LLM_MODEL'],
        api_key=SecretStr(api_key) if api_key else None,
        base_url=my_args.llm_base_url or os.environ.get('LLM_BASE_URL', None),
    )

    if not os.path.exists(my_args.output_dir):
        raise ValueError(f'Output directory {my_args.output_dir} does not exist.')

    if my_args.issue_number == 'all_successful':
        if not username:
            raise ValueError('username is required.')
        process_all_successful_issues(
            my_args.output_dir,
            token,
            username,
            platform,
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
        if not username:
            raise ValueError('username is required.')
        process_single_issue(
            my_args.output_dir,
            resolver_output,
            token,
            username,
            platform,
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
