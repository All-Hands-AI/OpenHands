from typing import Any

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Import models conditionally to handle different versions of the azure-devops package
try:
    from azure.devops.v5_1.git.models import GitPullRequest
    from azure.devops.v5_1.work_item_tracking.models import Wiql
except ImportError:
    # For testing purposes, create mock classes
    class GitPullRequest:  # type: ignore
        def __init__(
            self,
            source_ref_name=None,
            target_ref_name=None,
            title=None,
            description=None,
        ):
            self.source_ref_name = source_ref_name
            self.target_ref_name = target_ref_name
            self.title = title
            self.description = description

    class Wiql:  # type: ignore
        def __init__(self, query=None):
            self.query = query


from openhands.core.logger import openhands_logger as logger
from openhands.resolver.interfaces.issue import (
    Issue,
    IssueHandlerInterface,
    ReviewThread,
)


class AzureDevOpsIssueHandler(IssueHandlerInterface):
    def __init__(
        self,
        owner: str,
        repo: str,
        token: str,
        username: str | None = None,
        base_domain: str = 'dev.azure.com',
    ):
        """Initialize an Azure DevOps issue handler.

        Args:
            owner: The owner (organization) of the repository
            repo: The name of the repository (format: project/repo)
            token: The Azure DevOps personal access token
            username: Optional Azure DevOps username
            base_domain: The domain for Azure DevOps (default: "dev.azure.com")
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.username = username
        self.base_domain = base_domain

        # Parse the repository name (expected format: project/repo)
        parts = repo.split('/')
        if len(parts) != 2:
            raise ValueError(
                f'Invalid repository name format: {repo}. Expected format: project/repo'
            )

        self.project_name, self.repo_name = parts

        self.base_url = self.get_base_url()
        self.download_url = self.get_download_url()
        self.clone_url = self.get_clone_url()
        self.headers = self.get_headers()

        # Create a connection to Azure DevOps
        self.organization_url = f'https://{self.base_domain}/{self.owner}'
        self.credentials = BasicAuthentication('', self.token)
        self.connection = Connection(
            base_url=self.organization_url, creds=self.credentials
        )

    def set_owner(self, owner: str) -> None:
        self.owner = owner

    def get_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Basic {self.token}',
            'Accept': 'application/json',
        }

    def get_base_url(self) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.project_name}/_apis/git/repositories/{self.repo_name}'

    def get_authorize_url(self) -> str:
        return f'https://{self.username}:{self.token}@{self.base_domain}/'

    def get_branch_url(self, branch_name: str) -> str:
        return self.get_base_url() + f'/refs?filter=heads/{branch_name}'

    def get_download_url(self) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.project_name}/_apis/wit/workitems'

    def get_clone_url(self) -> str:
        return f'https://{self.username}:{self.token}@{self.base_domain}/{self.owner}/{self.project_name}/_git/{self.repo_name}'

    def get_graphql_url(self) -> str:
        return f'https://{self.base_domain}/{self.owner}/_apis/graphql'

    def get_compare_url(self, branch_name: str) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.project_name}/_git/{self.repo_name}/branchCompare?baseVersion=GC{self.get_default_branch_name()}&targetVersion=GC{branch_name}'

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Azure DevOps.

        Args:
            issue_numbers: The numbers of the issues to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Azure DevOps issues.
        """
        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [issue for issue in all_issues if issue['id'] in issue_numbers]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            # Check for required fields (id and title)
            if any(
                [
                    issue.get('fields', {}).get(key) is None
                    for key in ['System.Id', 'System.Title']
                ]
            ):
                logger.warning(f'Skipping issue {issue} as it is missing id or title.')
                continue

            # Handle empty body by using empty string
            description = issue.get('fields', {}).get('System.Description', '')
            if description is None:
                description = ''

            # Get issue thread comments
            thread_comments = self.get_issue_comments(
                issue['id'], comment_id=comment_id
            )

            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['id'],
                title=issue['fields']['System.Title'],
                body=description,
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues

    def download_issues(self) -> list[Any]:
        """Download issues from Azure DevOps.

        Returns:
            List of Azure DevOps issues.
        """
        # Use the Work Item Tracking client to get work items
        wit_client = self.connection.clients.get_work_item_tracking_client()

        # Create a WIQL query to get all open issues in the project
        wiql = Wiql(
            query=f"""
            select [System.Id],
                [System.WorkItemType],
                [System.Title],
                [System.State],
                [System.Description]
            from WorkItems
            where [System.TeamProject] = '{self.project_name}'
            and [System.WorkItemType] = 'Issue'
            and [System.State] <> 'Closed'
            and [System.State] <> 'Resolved'
            order by [System.ChangedDate] desc
            """
        )

        # Execute the query
        wiql_results = wit_client.query_by_wiql(wiql).work_items

        # Get the full work items
        all_issues = []
        if wiql_results:
            work_item_ids = [int(res.id) for res in wiql_results]
            work_items = wit_client.get_work_items(work_item_ids)

            for work_item in work_items:
                # Convert the work item to a dictionary format similar to GitHub/GitLab
                issue = {
                    'id': work_item.id,
                    'fields': work_item.fields,
                }
                all_issues.append(issue)

        return all_issues

    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific issue from Azure DevOps."""
        # Use the Work Item Tracking client to get work item comments
        wit_client = self.connection.clients.get_work_item_tracking_client()

        # Get the comments for the work item
        comments = wit_client.get_comments(self.project_name, issue_number)

        all_comments = []
        if comments and comments.comments:
            if comment_id:
                matching_comment = next(
                    (
                        comment.text
                        for comment in comments.comments
                        if comment.id == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments = [comment.text for comment in comments.comments]

        return all_comments if all_comments else None

    def branch_exists(self, branch_name: str) -> bool:
        logger.info(f'Checking if branch {branch_name} exists...')

        # Use the Git client to check if the branch exists
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return False

            # Get the branch
            branches = git_client.get_branches(repo.id, self.project_name)
            exists = any(b.name == branch_name for b in branches)

            logger.info(f'Branch {branch_name} exists: {exists}')
            return exists
        except Exception as e:
            logger.warning(f'Error checking if branch exists: {e}')
            return False

    def get_branch_name(self, base_branch_name: str) -> str:
        branch_name = base_branch_name
        attempt = 1
        while self.branch_exists(branch_name):
            attempt += 1
            branch_name = f'{base_branch_name}-try{attempt}'
        return branch_name

    def reply_to_comment(self, pr_number: int, comment_id: str, reply: str) -> None:
        # Use the Git client to reply to a comment
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            # Create a comment reply
            comment_reply = f'Openhands fix success summary\n\n\n{reply}'

            # Add the comment to the thread
            git_client.create_thread_comment(
                comment=comment_reply,
                repository_id=repo.id,
                pull_request_id=pr_number,
                thread_id=comment_id,
                project=self.project_name,
            )
        except Exception as e:
            logger.warning(f'Error replying to comment: {e}')

    def get_pull_url(self, pr_number: int) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.project_name}/_git/{self.repo_name}/pullrequest/{pr_number}'

    def get_default_branch_name(self) -> str:
        # Use the Git client to get the default branch
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return 'main'  # Default to 'main' if repository not found

            # Get the default branch
            return repo.default_branch.replace('refs/heads/', '')
        except Exception as e:
            logger.warning(f'Error getting default branch: {e}')
            return 'main'  # Default to 'main' if an error occurs

    def create_pull_request(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if data is None:
            data = {}

        # Use the Git client to create a pull request
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                raise RuntimeError(f'Repository not found: {self.repo_name}')

            # Create the pull request
            pr = GitPullRequest(
                source_ref_name=f'refs/heads/{data.get("head", "")}',
                target_ref_name=f'refs/heads/{data.get("base", "")}',
                title=data.get('title', ''),
                description=data.get('body', ''),
            )

            created_pr = git_client.create_pull_request(pr, repo.id, self.project_name)

            # Convert to a format similar to GitHub/GitLab
            pr_data = {
                'id': created_pr.pull_request_id,
                'number': created_pr.pull_request_id,
                'html_url': self.get_pull_url(created_pr.pull_request_id),
            }

            return pr_data
        except Exception as e:
            if '403' in str(e):
                raise RuntimeError(
                    'Failed to create pull request due to missing permissions. '
                    'Make sure that the provided token has push permissions for the repository.'
                )
            raise RuntimeError(f'Failed to create pull request: {e}')

    def request_reviewers(self, reviewer: str, pr_number: int) -> None:
        # Azure DevOps doesn't have a direct API for requesting reviewers
        # Instead, we'll add a comment mentioning the reviewer
        try:
            # Use the Git client to add a comment
            git_client = self.connection.clients.get_git_client()

            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            # Create a comment mentioning the reviewer
            comment = f'@{reviewer} Please review this pull request.'

            # Add the comment to the pull request
            git_client.create_thread(
                comment_thread={
                    'comments': [{'content': comment}],
                    'status': 'active',
                },
                repository_id=repo.id,
                pull_request_id=pr_number,
                project=self.project_name,
            )
        except Exception as e:
            logger.warning(f'Failed to request review from {reviewer}: {e}')

    def send_comment_msg(self, issue_number: int, msg: str) -> None:
        """Send a comment message to an Azure DevOps issue or pull request.

        Args:
            issue_number: The issue or pull request number
            msg: The message content to post as a comment
        """
        # Use the Work Item Tracking client to add a comment to a work item
        wit_client = self.connection.clients.get_work_item_tracking_client()

        try:
            # Add the comment to the work item
            wit_client.add_comment(self.project_name, issue_number, {'text': msg})
            logger.info(f'Comment added to the issue: {msg}')
        except Exception as e:
            logger.error(f'Failed to post comment: {e}')

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


class AzureDevOpsPRHandler(AzureDevOpsIssueHandler):
    def __init__(
        self,
        owner: str,
        repo: str,
        token: str,
        username: str | None = None,
        base_domain: str = 'dev.azure.com',
    ):
        """Initialize an Azure DevOps PR handler.

        Args:
            owner: The owner (organization) of the repository
            repo: The name of the repository (format: project/repo)
            token: The Azure DevOps personal access token
            username: Optional Azure DevOps username
            base_domain: The domain for Azure DevOps (default: "dev.azure.com")
        """
        super().__init__(owner, repo, token, username, base_domain)

    def download_issues(self) -> list[Any]:
        """Download pull requests from Azure DevOps.

        Returns:
            List of Azure DevOps pull requests as issues.
        """
        # Use the Git client to get pull requests
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return []

            # Get all active pull requests for the repository
            pull_requests = git_client.get_pull_requests(
                repo.id, status='active', project=self.project_name
            )

            # Convert pull requests to the issue format
            all_issues = []
            for pr in pull_requests:
                # Convert the PR to a dictionary format similar to issues
                issue = {
                    'id': pr.pull_request_id,
                    'fields': {
                        'System.Id': pr.pull_request_id,
                        'System.Title': pr.title,
                        'System.Description': pr.description or '',
                    },
                    'source_branch': pr.source_ref_name,
                    'repository': pr.repository,
                }
                all_issues.append(issue)

            return all_issues

        except Exception as e:
            logger.warning(f'Error downloading pull requests: {e}')
            return []

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download pull requests from Azure DevOps.

        Args:
            issue_numbers: The numbers of the pull requests to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Azure DevOps pull requests as Issue objects.
        """
        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [issue for issue in all_issues if issue['id'] in issue_numbers]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            # Get PR metadata
            (
                closing_issues,
                closing_issue_numbers,
                review_bodies,
                review_threads,
                thread_ids,
            ) = self.download_pr_metadata(issue['id'], comment_id)

            # Create the Issue object
            converted_issue = Issue(
                number=issue['id'],
                title=issue['fields']['System.Title'],
                body=issue['fields']['System.Description'],
                owner=self.owner,
                repo=f'{self.project_name}/{self.repo_name}',
                head_branch=issue['source_branch'].replace('refs/heads/', ''),
                closing_issues=closing_issues,
                closing_issue_numbers=closing_issue_numbers,
                review_bodies=review_bodies,
                review_threads=review_threads,
                thread_ids=thread_ids,
            )
            converted_issues.append(converted_issue)

        return converted_issues

    def download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str] | None, list[ReviewThread], list[str]]:
        """Get metadata for a pull request.

        Args:
            pull_number: The number of the pull request to query.
            comment_id: Optional ID of a specific comment to focus on.

        Returns:
            Tuple containing:
            1. List of closing issue bodies
            2. List of closing issue numbers
            3. List of review bodies
            4. List of review threads
            5. List of thread IDs
        """
        # Use the Git client to get pull request information
        git_client = self.connection.clients.get_git_client()

        try:
            # Get the repository ID
            repos = git_client.get_repositories(self.project_name)
            repo = next(
                (r for r in repos if r.name.lower() == self.repo_name.lower()), None
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return [], [], None, [], []

            # Get the pull request
            git_client.get_pull_request(repo.id, pull_number, self.project_name)

            # Get work items associated with the pull request
            work_items = git_client.get_pull_request_work_items(
                repo.id, pull_number, self.project_name
            )

            # Get the work item details
            wit_client = self.connection.clients.get_work_item_tracking_client()
            closing_issues = []
            closing_issue_numbers = []

            if work_items:
                work_item_ids = [int(item.id) for item in work_items]
                work_item_details = wit_client.get_work_items(work_item_ids)

                for work_item in work_item_details:
                    closing_issues.append(
                        work_item.fields.get('System.Description', '')
                    )
                    closing_issue_numbers.append(work_item.id)

            # Get pull request threads (comments)
            threads = git_client.get_threads(repo.id, pull_number, self.project_name)

            # Process review comments
            review_bodies = None
            review_threads = []
            thread_ids = []

            for thread in threads:
                if thread.status == 'active' and not thread.is_deleted:
                    # Check if this thread contains the specific comment we're looking for
                    thread_contains_comment_id = False
                    if comment_id is not None:
                        thread_contains_comment_id = any(
                            comment.id == comment_id for comment in thread.comments
                        )

                    # If we're looking for a specific comment and this thread doesn't have it, skip
                    if comment_id is not None and not thread_contains_comment_id:
                        continue

                    # Process the thread
                    comments = [
                        comment.content
                        for comment in thread.comments
                        if comment.content
                    ]
                    if comments:
                        files = []
                        if thread.thread_context and thread.thread_context.file_path:
                            files.append(thread.thread_context.file_path)

                        review_thread = ReviewThread(
                            comment='\n'.join(comments),
                            files=files,
                        )
                        review_threads.append(review_thread)
                        thread_ids.append(str(thread.id))

            return (
                closing_issues,
                closing_issue_numbers,
                review_bodies,
                review_threads,
                thread_ids,
            )

        except Exception as e:
            logger.warning(f'Error getting pull request metadata: {e}')
            return [], [], None, [], []
