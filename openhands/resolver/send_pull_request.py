import argparse
import json
import os
import subprocess

import jinja2
from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import ProviderType
from openhands.llm.llm import LLM
from openhands.resolver.interfaces.bitbucket import BitbucketIssueHandler
from openhands.resolver.interfaces.github import GithubIssueHandler
from openhands.resolver.interfaces.gitlab import GitlabIssueHandler
from openhands.resolver.interfaces.issue import Issue
from openhands.resolver.interfaces.issue_definitions import ServiceContextIssue
from openhands.resolver.io_utils import (
    load_single_resolver_output,
)
from openhands.resolver.pull_request_sender import PullRequestSender
from openhands.resolver.resolver_output import ResolverOutput
from openhands.resolver.utils import identify_token
from openhands.utils.async_utils import GENERAL_TIMEOUT, call_async_from_sync


# Legacy function - kept for backward compatibility
def apply_patch(repo_dir: str, patch: str) -> None:
    """Apply a patch to a repository.

    Args:
        repo_dir: The directory containing the repository
        patch: The patch to apply
    """
    # This is now a wrapper function for backward compatibility
    # Create a temporary PullRequestSender instance to use the method
    from argparse import Namespace
    args = Namespace(
        token=None, username=None, output_dir='.', pr_type='draft', issue_number='0',
        fork_owner=None, send_on_failure=False, target_branch=None, reviewer=None,
        pr_title=None, base_domain=None, git_user_name='openhands',
        git_user_email='openhands@all-hands.dev', llm_model=None, llm_api_key=None,
        llm_base_url=None
    )
    try:
        sender = PullRequestSender(args)
        sender.apply_patch(repo_dir, patch)
    except ValueError:
        # If PullRequestSender fails due to missing args, fall back to direct implementation
        from openhands.resolver.patching import apply_diff, parse_patch
        from openhands.core.logger import openhands_logger as logger
        import os
        import shutil
        
        diffs = parse_patch(patch)
        for diff in diffs:
            if not diff.header.new_path:
                logger.warning('Could not determine file to patch')
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
                    logger.info(f'Deleted file: {old_path}')
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
                logger.warning(f'No changes to apply for {old_path}')
                continue

            new_content = apply_diff(diff, split_content)

            # Ensure the directory exists before writing the file
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # Write the new content using the detected line endings
            with open(new_path, 'w', newline=newline) as f:
                for line in new_content:
                    print(line, file=f)

        logger.info('Patch applied successfully')


# Legacy function - kept for backward compatibility
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
    # Create a temporary PullRequestSender instance
    from argparse import Namespace
    args = Namespace(
        token=None, username=None, output_dir=output_dir, pr_type='draft', issue_number=str(issue_number),
        fork_owner=None, send_on_failure=False, target_branch=None, reviewer=None,
        pr_title=None, base_domain=None, git_user_name='openhands',
        git_user_email='openhands@all-hands.dev', llm_model=None, llm_api_key=None,
        llm_base_url=None
    )
    try:
        sender = PullRequestSender(args)
        return sender.initialize_repo(issue_number, issue_type, base_commit)
    except ValueError:
        # Fall back to direct implementation if PullRequestSender fails
        from openhands.core.logger import openhands_logger as logger
        import os
        import shutil
        import subprocess
        
        src_dir = os.path.join(output_dir, 'repo')
        dest_dir = os.path.join(output_dir, 'patches', f'{issue_type}_{issue_number}')

        if not os.path.exists(src_dir):
            raise ValueError(f'Source directory {src_dir} does not exist.')

        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)

        shutil.copytree(src_dir, dest_dir)
        logger.info(f'Copied repository to {dest_dir}')

        # Checkout the base commit if provided
        if base_commit:
            result = subprocess.run(
                f'git -C {dest_dir} checkout {base_commit}',
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.info(f'Error checking out commit: {result.stderr}')
                raise RuntimeError('Failed to check out commit')

        return dest_dir


# Legacy function - kept for backward compatibility
def make_commit(
    repo_dir: str,
    issue: Issue,
    issue_type: str,
    git_user_name: str = 'openhands',
    git_user_email: str = 'openhands@all-hands.dev',
) -> None:
    """Make a commit with the changes to the repository.

    Args:
        repo_dir: The directory containing the repository
        issue: The issue to fix
        issue_type: The type of the issue
        git_user_name: Git username for commits
        git_user_email: Git email for commits
    """
    # Create a temporary PullRequestSender instance
    from argparse import Namespace
    args = Namespace(
        token=None, username=None, output_dir='.', pr_type='draft', issue_number=str(issue.number),
        fork_owner=None, send_on_failure=False, target_branch=None, reviewer=None,
        pr_title=None, base_domain=None, git_user_name=git_user_name,
        git_user_email=git_user_email, llm_model=None, llm_api_key=None,
        llm_base_url=None
    )
    try:
        sender = PullRequestSender(args)
        sender.make_commit(repo_dir, issue, issue_type)
    except ValueError:
        # Fall back to direct implementation
        from openhands.core.logger import openhands_logger as logger
        import subprocess
        
        # Check if git username is set
        result = subprocess.run(
            f'git -C {repo_dir} config user.name',
            shell=True,
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            # If username is not set, configure git with the provided credentials
            subprocess.run(
                f'git -C {repo_dir} config user.name "{git_user_name}" && '
                f'git -C {repo_dir} config user.email "{git_user_email}" && '
                f'git -C {repo_dir} config alias.git "git --no-pager"',
                shell=True,
                check=True,
            )
            logger.info(f'Git user configured as {git_user_name} <{git_user_email}>')

        # Add all changes to the git index
        result = subprocess.run(
            f'git -C {repo_dir} add .', shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f'Error adding files: {result.stderr}')
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
            logger.error(
                f'No changes to commit for issue #{issue.number}. Skipping commit.'
            )
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


# Legacy function - kept for backward compatibility
def send_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: ProviderType,
    patch_dir: str,
    pr_type: str,
    fork_owner: str | None = None,
    additional_message: str | None = None,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
    base_domain: str | None = None,
    git_user_name: str = 'openhands',
    git_user_email: str = 'openhands@all-hands.dev',
) -> str:
    """Send a pull request to a GitHub, GitLab, or Bitbucket repository.

    Args:
        issue: The issue to send the pull request for
        token: The token to use for authentication
        username: The username, if provided
        platform: The platform of the repository.
        patch_dir: The directory containing the patches to apply
        pr_type: The type: branch (no PR created), draft or ready (regular PR created)
        fork_owner: The owner of the fork to push changes to (if different from the original repo owner)
        additional_message: The additional messages to post as a comment on the PR in json list format
        target_branch: The target branch to create the pull request against (defaults to repository default branch)
        reviewer: The username of the reviewer to assign
        pr_title: Custom title for the pull request (optional)
        base_domain: The base domain for the git server (defaults to "github.com" for GitHub, "gitlab.com" for GitLab, and "bitbucket.org" for Bitbucket)
        git_user_name: Git username for commits
        git_user_email: Git email for commits
    """
    # Create a temporary PullRequestSender instance
    from argparse import Namespace
    args = Namespace(
        token=token, username=username, output_dir=os.path.dirname(patch_dir), 
        pr_type=pr_type, issue_number=str(issue.number),
        fork_owner=fork_owner, send_on_failure=False, target_branch=target_branch, 
        reviewer=reviewer, pr_title=pr_title, base_domain=base_domain, 
        git_user_name=git_user_name, git_user_email=git_user_email, 
        llm_model=None, llm_api_key=None, llm_base_url=None
    )
    sender = PullRequestSender(args)
    return sender.send_pull_request(issue, patch_dir, additional_message)


# Legacy function - kept for backward compatibility
def update_existing_pull_request(
    issue: Issue,
    token: str,
    username: str | None,
    platform: ProviderType,
    patch_dir: str,
    llm_config: LLMConfig,
    comment_message: str | None = None,
    additional_message: str | None = None,
    base_domain: str | None = None,
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
        base_domain: The base domain for the git server (defaults to "github.com" for GitHub and "gitlab.com" for GitLab)
    """
    # Create a temporary PullRequestSender instance
    from argparse import Namespace
    args = Namespace(
        token=token, username=username, output_dir=os.path.dirname(patch_dir), 
        pr_type='draft', issue_number=str(issue.number), fork_owner=None, 
        send_on_failure=False, target_branch=None, reviewer=None, pr_title=None, 
        base_domain=base_domain, git_user_name='openhands', 
        git_user_email='openhands@all-hands.dev', llm_model=llm_config.model if llm_config else None, 
        llm_api_key=llm_config.api_key.get_secret_value() if llm_config and llm_config.api_key else None, 
        llm_base_url=llm_config.base_url if llm_config else None
    )
    sender = PullRequestSender(args)
    return sender.update_existing_pull_request(issue, patch_dir, comment_message, additional_message)


# Legacy function - kept for backward compatibility
def process_single_issue(
    output_dir: str,
    resolver_output: ResolverOutput,
    token: str,
    username: str,
    platform: ProviderType,
    pr_type: str,
    llm_config: LLMConfig,
    fork_owner: str | None,
    send_on_failure: bool,
    target_branch: str | None = None,
    reviewer: str | None = None,
    pr_title: str | None = None,
    base_domain: str | None = None,
    git_user_name: str = 'openhands',
    git_user_email: str = 'openhands@all-hands.dev',
) -> None:
    """Process a single issue and send a pull request."""
    # Create a temporary PullRequestSender instance
    from argparse import Namespace
    args = Namespace(
        token=token, username=username, output_dir=output_dir, pr_type=pr_type, 
        issue_number=str(resolver_output.issue.number), fork_owner=fork_owner, 
        send_on_failure=send_on_failure, target_branch=target_branch, reviewer=reviewer, 
        pr_title=pr_title, base_domain=base_domain, git_user_name=git_user_name, 
        git_user_email=git_user_email, llm_model=llm_config.model if llm_config else None, 
        llm_api_key=llm_config.api_key.get_secret_value() if llm_config and llm_config.api_key else None, 
        llm_base_url=llm_config.base_url if llm_config else None
    )
    sender = PullRequestSender(args)
    sender.process_single_issue(resolver_output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Send a pull request to Github or Gitlab.'
    )
    parser.add_argument(
        '--selected-repo',
        type=str,
        default=None,
        help='repository to send pull request in form of `owner/repo`.',
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
    parser.add_argument(
        '--base-domain',
        type=str,
        default=None,
        help='Base domain for the git server (defaults to "github.com" for GitHub and "gitlab.com" for GitLab)',
    )
    parser.add_argument(
        '--git-user-name',
        type=str,
        default='openhands',
        help='Git user name for commits',
    )
    parser.add_argument(
        '--git-user-email',
        type=str,
        default='openhands@all-hands.dev',
        help='Git user email for commits',
    )
    my_args = parser.parse_args()

    # Create and run PullRequestSender
    sender = PullRequestSender(my_args)
    sender.run()


if __name__ == '__main__':
    main()
