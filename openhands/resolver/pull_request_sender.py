import json
import os
import shutil
import subprocess
from argparse import Namespace
from typing import cast

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
from openhands.resolver.patching import apply_diff, parse_patch
from openhands.resolver.resolver_output import ResolverOutput
from openhands.resolver.utils import identify_token
from openhands.utils.async_utils import GENERAL_TIMEOUT, call_async_from_sync


class PullRequestSender:
    """Class for handling pull request sending operations."""

    def __init__(self, args: Namespace) -> None:
        """Initialize the PullRequestSender with the given parameters."""
        self.token = (
            args.token or os.getenv('GITHUB_TOKEN') or os.getenv('GITLAB_TOKEN')
        )
        if not self.token:
            raise ValueError(
                'token is not set, set via --token or GITHUB_TOKEN or GITLAB_TOKEN environment variable.'
            )

        self.username = args.username if args.username else os.getenv('GIT_USERNAME')
        if not self.username:
            raise ValueError('username is required.')

        self.platform = call_async_from_sync(
            identify_token,
            GENERAL_TIMEOUT,
            self.token,
            args.base_domain,
        )

        self.output_dir = args.output_dir
        if not os.path.exists(self.output_dir):
            raise ValueError(f'Output directory {self.output_dir} does not exist.')

        self.pr_type = args.pr_type
        self.issue_number = int(args.issue_number)
        self.fork_owner = args.fork_owner
        self.send_on_failure = args.send_on_failure
        self.target_branch = args.target_branch
        self.reviewer = args.reviewer
        self.pr_title = args.pr_title
        self.base_domain = args.base_domain
        # Set git configuration with defaults if None
        self.git_user_name = args.git_user_name or 'openhands'
        self.git_user_email = args.git_user_email or 'openhands@all-hands.dev'

        # Configure LLM - only if API key and model are available
        api_key = args.llm_api_key or os.environ.get('LLM_API_KEY')
        model = args.llm_model or os.environ.get('LLM_MODEL')
        if api_key and model:
            self.llm_config = LLMConfig(
                model=model,
                api_key=SecretStr(api_key),
                base_url=args.llm_base_url or os.environ.get('LLM_BASE_URL', None),
            )
        else:
            self.llm_config = None

    def apply_patch(self, repo_dir: str, patch: str) -> None:
        """Apply a patch to a repository.

        Args:
            repo_dir: The directory containing the repository
            patch: The patch to apply
        """
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

    def initialize_repo(
        self, issue_number: int, issue_type: str, base_commit: str | None = None
    ) -> str:
        """Initialize the repository.

        Args:
            issue_number: The issue number to fix
            issue_type: The type of the issue
            base_commit: The base commit to checkout (if issue_type is pr)
        """
        src_dir = os.path.join(self.output_dir, 'repo')
        dest_dir = os.path.join(
            self.output_dir, 'patches', f'{issue_type}_{issue_number}'
        )

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

    def make_commit(
        self,
        repo_dir: str,
        issue: Issue,
        issue_type: str,
    ) -> None:
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
            # If username is not set, configure git with the provided credentials
            subprocess.run(
                f'git -C {repo_dir} config user.name "{self.git_user_name}" && '
                f'git -C {repo_dir} config user.email "{self.git_user_email}" && '
                f'git -C {repo_dir} config alias.git "git --no-pager"',
                shell=True,
                check=True,
            )
            logger.info(
                f'Git user configured as {self.git_user_name} <{self.git_user_email}>'
            )

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

    def send_pull_request(
        self,
        issue: Issue,
        patch_dir: str,
        additional_message: str | None = None,
    ) -> str:
        """Send a pull request to a GitHub, GitLab, or Bitbucket repository.

        Args:
            issue: The issue to send the pull request for
            patch_dir: The directory containing the patches to apply
            additional_message: The additional messages to post as a comment on the PR in json list format
        """
        if self.pr_type not in ['branch', 'draft', 'ready']:
            raise ValueError(f'Invalid pr_type: {self.pr_type}')

        # Determine default base_domain based on platform
        base_domain = self.base_domain
        if base_domain is None:
            if self.platform == ProviderType.GITHUB:
                base_domain = 'github.com'
            elif self.platform == ProviderType.GITLAB:
                base_domain = 'gitlab.com'
            else:  # platform == ProviderType.BITBUCKET
                base_domain = 'bitbucket.org'

        # At this point, base_domain is guaranteed to be a string
        base_domain = cast(str, base_domain)

        # Create the appropriate handler based on platform
        handler = None
        if self.platform == ProviderType.GITHUB:
            handler = ServiceContextIssue(
                GithubIssueHandler(
                    issue.owner, issue.repo, self.token, self.username, base_domain
                ),
                None,
            )
        elif self.platform == ProviderType.GITLAB:
            handler = ServiceContextIssue(
                GitlabIssueHandler(
                    issue.owner, issue.repo, self.token, self.username, base_domain
                ),
                None,
            )
        elif self.platform == ProviderType.BITBUCKET:
            handler = ServiceContextIssue(
                BitbucketIssueHandler(
                    issue.owner, issue.repo, self.token, self.username, base_domain
                ),
                None,
            )
        else:
            raise ValueError(f'Unsupported platform: {self.platform}')

        # Create a new branch with a unique name
        base_branch_name = f'openhands-fix-issue-{issue.number}'
        branch_name = handler.get_branch_name(
            base_branch_name=base_branch_name,
        )

        # Get the default branch or use specified target branch
        logger.info('Getting base branch...')
        if self.target_branch:
            base_branch = self.target_branch
            exists = handler.branch_exists(branch_name=self.target_branch)
            if not exists:
                raise ValueError(f'Target branch {self.target_branch} does not exist')
        else:
            base_branch = handler.get_default_branch_name()
        logger.info(f'Base branch: {base_branch}')

        # Create and checkout the new branch
        logger.info('Creating new branch...')
        result = subprocess.run(
            ['git', '-C', patch_dir, 'checkout', '-b', branch_name],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f'Error creating new branch: {result.stderr}')
            raise RuntimeError(
                f'Failed to create a new branch {branch_name} in {patch_dir}:'
            )

        # Determine the repository to push to (original or fork)
        push_owner = self.fork_owner if self.fork_owner else issue.owner

        handler._strategy.set_owner(push_owner)

        logger.info('Pushing changes...')
        push_url = handler.get_clone_url()
        result = subprocess.run(
            ['git', '-C', patch_dir, 'push', push_url, branch_name],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f'Error pushing changes: {result.stderr}')
            raise RuntimeError('Failed to push changes to the remote repository')

        # Prepare the PR data: title and body
        final_pr_title = (
            self.pr_title
            if self.pr_title
            else f'Fix issue #{issue.number}: {issue.title}'
        )
        pr_body = f'This pull request fixes #{issue.number}.'
        if additional_message:
            pr_body += f'\n\n{additional_message}'
        pr_body += '\n\nAutomatic fix generated by [OpenHands](https://github.com/All-Hands-AI/OpenHands/) 🙌'

        # For cross repo pull request, we need to send head parameter like fork_owner:branch as per git documentation here : https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request
        # head parameter usage : The name of the branch where your changes are implemented. For cross-repository pull requests in the same network, namespace head with a user like this: username:branch.
        if self.fork_owner and self.platform == ProviderType.GITHUB:
            head_branch = f'{self.fork_owner}:{branch_name}'
        else:
            head_branch = branch_name
        # If we are not sending a PR, we can finish early and return the
        # URL for the user to open a PR manually
        if self.pr_type == 'branch':
            url = handler.get_compare_url(branch_name)
        else:
            # Prepare the PR for the GitHub API
            data = {
                'title': final_pr_title,
                (
                    'body' if self.platform == ProviderType.GITHUB else 'description'
                ): pr_body,
                (
                    'head' if self.platform == ProviderType.GITHUB else 'source_branch'
                ): head_branch,
                (
                    'base' if self.platform == ProviderType.GITHUB else 'target_branch'
                ): base_branch,
                'draft': self.pr_type == 'draft',
            }

            pr_data = handler.create_pull_request(data)
            url = pr_data['html_url']

            # Request review if a reviewer was specified
            if self.reviewer and self.pr_type != 'branch':
                number = pr_data['number']
                handler.request_reviewers(self.reviewer, number)

        logger.info(
            f'{self.pr_type} created: {url}\n\n--- Title: {final_pr_title}\n\n--- Body:\n{pr_body}'
        )

        return url

    def update_existing_pull_request(
        self,
        issue: Issue,
        patch_dir: str,
        comment_message: str | None = None,
        additional_message: str | None = None,
    ) -> str:
        """Update an existing pull request with the new patches.

        Args:
            issue: The issue to update.
            patch_dir: The directory containing the patches to apply.
            comment_message: The main message to post as a comment on the PR.
            additional_message: The additional messages to post as a comment on the PR in json list format.
        """
        # Determine default base_domain based on platform
        base_domain = self.base_domain
        if base_domain is None:
            base_domain = (
                'github.com' if self.platform == ProviderType.GITHUB else 'gitlab.com'
            )

        # At this point, base_domain is guaranteed to be a string
        base_domain = cast(str, base_domain)

        handler = None
        if self.platform == ProviderType.GITHUB:
            handler = ServiceContextIssue(
                GithubIssueHandler(
                    issue.owner, issue.repo, self.token, self.username, base_domain
                ),
                self.llm_config,
            )
        else:  # platform == Platform.GITLAB
            handler = ServiceContextIssue(
                GitlabIssueHandler(
                    issue.owner, issue.repo, self.token, self.username, base_domain
                ),
                self.llm_config,
            )

        branch_name = issue.head_branch

        # Prepare the push command
        push_command = (
            f'git -C {patch_dir} push '
            f'{handler.get_authorize_url()}'
            f'{issue.owner}/{issue.repo}.git {branch_name}'
        )

        # Push the changes to the existing branch
        result = subprocess.run(
            push_command, shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f'Error pushing changes: {result.stderr}')
            raise RuntimeError('Failed to push changes to the remote repository')

        pr_url = handler.get_pull_url(issue.number)
        logger.info(f'Updated pull request {pr_url} with new patches.')

        # Generate a summary of all comment success indicators for PR message
        if not comment_message and additional_message:
            try:
                explanations = json.loads(additional_message)
                if explanations:
                    comment_message = 'OpenHands made the following changes to resolve the issues:\n\n'
                    for explanation in explanations:
                        comment_message += f'- {explanation}\n'

                    # Summarize with LLM if provided
                    if self.llm_config is not None:
                        llm = LLM(self.llm_config)
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
                msg = f'Error occurred when replying to threads; success explanations {additional_message}'
                handler.send_comment_msg(issue.number, msg)

        return pr_url

    def process_single_issue(
        self,
        resolver_output: ResolverOutput,
    ) -> None:
        """Process a single issue and send a pull request."""
        # Determine default base_domain based on platform
        if self.base_domain is None:
            self.base_domain = (
                'github.com' if self.platform == ProviderType.GITHUB else 'gitlab.com'
            )

        if not resolver_output.success and not self.send_on_failure:
            logger.info(
                f'Issue {resolver_output.issue.number} was not successfully resolved. Skipping PR creation.'
            )
            return

        issue_type = resolver_output.issue_type

        if issue_type == 'issue':
            patched_repo_dir = self.initialize_repo(
                resolver_output.issue.number,
                issue_type,
                resolver_output.base_commit,
            )
        elif issue_type == 'pr':
            patched_repo_dir = self.initialize_repo(
                resolver_output.issue.number,
                issue_type,
                resolver_output.issue.head_branch,
            )
        else:
            raise ValueError(f'Invalid issue type: {issue_type}')

        self.apply_patch(patched_repo_dir, resolver_output.git_patch)

        self.make_commit(
            patched_repo_dir,
            resolver_output.issue,
            issue_type,
        )

        if issue_type == 'pr':
            self.update_existing_pull_request(
                issue=resolver_output.issue,
                patch_dir=patched_repo_dir,
                additional_message=resolver_output.result_explanation,
            )
        else:
            self.send_pull_request(
                issue=resolver_output.issue,
                patch_dir=patched_repo_dir,
                additional_message=resolver_output.result_explanation,
            )

    def run(self) -> None:
        """Main entry point for the PullRequestSender."""
        output_path = os.path.join(self.output_dir, 'output.jsonl')
        resolver_output = load_single_resolver_output(output_path, self.issue_number)
        self.process_single_issue(resolver_output)
