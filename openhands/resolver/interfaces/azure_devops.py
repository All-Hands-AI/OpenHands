import asyncio
import base64
from typing import Any

import httpx

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import RequestMethod
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

        # Set up API base URL
        self.api_base_url = f'https://{self.base_domain}/{self.owner}/_apis'

    def set_owner(self, owner: str) -> None:
        self.owner = owner

    def get_headers(self) -> dict[str, str]:
        # Azure DevOps uses Basic authentication with PAT
        # Username can be empty, password is the PAT
        credentials = base64.b64encode(f':{self.token}'.encode()).decode()
        return {
            'Authorization': f'Basic {credentials}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    async def _make_api_request(
        self,
        url: str,
        method: RequestMethod = RequestMethod.GET,
        params: dict | None = None,
        json_data: dict | None = None,
    ) -> dict | list | None:
        """Make an HTTP request to the Azure DevOps API."""
        try:
            async with httpx.AsyncClient() as client:
                if method == RequestMethod.GET:
                    response = await client.get(
                        url, headers=self.headers, params=params
                    )
                elif method == RequestMethod.POST:
                    response = await client.post(
                        url, headers=self.headers, params=params, json=json_data
                    )
                else:
                    raise ValueError(f'Unsupported HTTP method: {method}')

                if response.status_code >= 400:
                    logger.error(
                        f'Azure DevOps API error: {response.status_code} - {response.text}'
                    )
                    return None

                try:
                    return response.json()
                except Exception:
                    return response.text

        except httpx.RequestError as e:
            logger.error(f'Request error: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error: {e}')
            return None

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
        """Download issues from Azure DevOps using HTTP API calls."""
        return asyncio.run(self._download_issues_async())

    async def _download_issues_async(self) -> list[Any]:
        """Download issues from Azure DevOps asynchronously."""
        # Use WIQL to query for open bugs
        wiql_url = f'{self.api_base_url}/wit/wiql'
        wiql_params = {'api-version': '7.1-preview.2'}

        wiql_query = {
            'query': f"""
                select [System.Id],
                    [System.WorkItemType],
                    [System.Title],
                    [System.State],
                    [System.Description]
                from WorkItems
                where [System.TeamProject] = '{self.project_name}'
                and [System.WorkItemType] in ('Bug', 'Issue', 'Task')
                and [System.State] <> 'Closed'
                and [System.State] <> 'Resolved'
                and [System.State] <> 'Done'
                order by [System.ChangedDate] desc
            """
        }

        wiql_data = await self._make_api_request(
            wiql_url,
            method=RequestMethod.POST,
            params=wiql_params,
            json_data=wiql_query,
        )

        if not wiql_data or not isinstance(wiql_data, dict):
            return []

        work_items = wiql_data.get('workItems', [])

        # Get full work item details
        all_issues = []
        for work_item in work_items:
            work_item_id = work_item.get('id')
            if not work_item_id:
                continue

            # Get work item details
            work_item_url = f'{self.api_base_url}/wit/workitems/{work_item_id}'
            work_item_params = {'api-version': '7.1-preview.3'}

            work_item_data = await self._make_api_request(
                work_item_url, params=work_item_params
            )

            if work_item_data and isinstance(work_item_data, dict):
                # Convert the work item to a dictionary format similar to GitHub/GitLab
                issue = {
                    'id': work_item_data.get('id'),
                    'fields': work_item_data.get('fields', {}),
                }
                all_issues.append(issue)

        return all_issues

    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific issue from Azure DevOps."""
        return asyncio.run(self._get_issue_comments_async(issue_number, comment_id))

    async def _get_issue_comments_async(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific issue from Azure DevOps asynchronously."""
        # Get the comments for the work item
        comments_url = f'{self.api_base_url}/wit/workItems/{issue_number}/comments'
        comments_params = {'api-version': '7.1-preview.3'}

        comments_data = await self._make_api_request(
            comments_url, params=comments_params
        )

        if not comments_data or not isinstance(comments_data, dict):
            return None

        comments = comments_data.get('comments', [])

        all_comments = []
        if comments:
            if comment_id:
                matching_comment = next(
                    (
                        comment.get('text', '')
                        for comment in comments
                        if comment.get('id') == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments = [
                    comment.get('text', '')
                    for comment in comments
                    if comment.get('text')
                ]

        return all_comments if all_comments else None

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists."""
        return asyncio.run(self._branch_exists_async(branch_name))

    async def _branch_exists_async(self, branch_name: str) -> bool:
        """Check if a branch exists asynchronously."""
        logger.info(f'Checking if branch {branch_name} exists...')

        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return False

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return False

            repo_id = repo.get('id')

            # Get the branches (refs) for the repository
            refs_url = f'{self.api_base_url}/git/repositories/{repo_id}/refs'
            refs_params = {
                'api-version': '7.1-preview.1',
                'filter': f'heads/{branch_name}',
            }

            refs_data = await self._make_api_request(refs_url, params=refs_params)

            if not refs_data or not isinstance(refs_data, dict):
                return False

            refs = refs_data.get('value', [])
            exists = len(refs) > 0

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
        """Reply to a comment on a pull request."""
        asyncio.run(self._reply_to_comment_async(pr_number, comment_id, reply))

    async def _reply_to_comment_async(
        self, pr_number: int, comment_id: str, reply: str
    ) -> None:
        """Reply to a comment on a pull request asynchronously."""
        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            repo_id = repo.get('id')

            # Create a comment reply
            comment_reply = f'Openhands fix success summary\n\n\n{reply}'

            # Add the comment to the thread
            comment_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullRequests/{pr_number}/threads/{comment_id}/comments'
            comment_params = {'api-version': '7.1-preview.1'}
            comment_data = {'content': comment_reply}

            await self._make_api_request(
                comment_url,
                method=RequestMethod.POST,
                params=comment_params,
                json_data=comment_data,
            )
        except Exception as e:
            logger.warning(f'Error replying to comment: {e}')

    def get_pull_url(self, pr_number: int) -> str:
        return f'https://{self.base_domain}/{self.owner}/{self.project_name}/_git/{self.repo_name}/pullrequest/{pr_number}'

    def get_default_branch_name(self) -> str:
        """Get the default branch name."""
        return asyncio.run(self._get_default_branch_name_async())

    async def _get_default_branch_name_async(self) -> str:
        """Get the default branch name asynchronously."""
        try:
            # First, get the repository
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return 'main'  # Default to 'main' if repository not found

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return 'main'  # Default to 'main' if repository not found

            # Get the default branch
            default_branch = repo.get('defaultBranch', 'refs/heads/main')
            return default_branch.replace('refs/heads/', '')
        except Exception as e:
            logger.warning(f'Error getting default branch: {e}')
            return 'main'  # Default to 'main' if an error occurs

    def create_pull_request(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a pull request."""
        return asyncio.run(self._create_pull_request_async(data))

    async def _create_pull_request_async(
        self, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Create a pull request asynchronously."""
        if data is None:
            data = {}

        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                raise RuntimeError(f'Repository not found: {self.repo_name}')

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                raise RuntimeError(f'Repository not found: {self.repo_name}')

            repo_id = repo.get('id')

            # Create the pull request
            pr_data = {
                'sourceRefName': f'refs/heads/{data.get("head", "")}',
                'targetRefName': f'refs/heads/{data.get("base", "")}',
                'title': data.get('title', ''),
                'description': data.get('body', ''),
            }

            pr_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullrequests'
            pr_params = {'api-version': '7.1-preview.1'}

            created_pr = await self._make_api_request(
                pr_url, method=RequestMethod.POST, params=pr_params, json_data=pr_data
            )

            if not created_pr or not isinstance(created_pr, dict):
                raise RuntimeError('Failed to create pull request')

            # Convert to a format similar to GitHub/GitLab
            pr_id = created_pr.get('pullRequestId')
            if pr_id is None:
                raise RuntimeError('Pull request ID not found in response')

            pr_result = {
                'id': pr_id,
                'number': pr_id,
                'html_url': self.get_pull_url(pr_id),
            }

            return pr_result
        except Exception as e:
            if '403' in str(e):
                raise RuntimeError(
                    'Failed to create pull request due to missing permissions. '
                    'Make sure that the provided token has push permissions for the repository.'
                )
            raise RuntimeError(f'Failed to create pull request: {e}')

    def request_reviewers(self, reviewer: str, pr_number: int) -> None:
        """Request reviewers for a pull request."""
        asyncio.run(self._request_reviewers_async(reviewer, pr_number))

    async def _request_reviewers_async(self, reviewer: str, pr_number: int) -> None:
        """Request reviewers for a pull request asynchronously."""
        # Azure DevOps doesn't have a direct API for requesting reviewers
        # Instead, we'll add a comment mentioning the reviewer
        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return

            repo_id = repo.get('id')

            # Create a comment mentioning the reviewer
            comment = f'@{reviewer} Please review this pull request.'

            # Add the comment to the pull request
            thread_data = {
                'comments': [{'content': comment}],
                'status': 'active',
            }

            thread_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullRequests/{pr_number}/threads'
            thread_params = {'api-version': '7.1-preview.1'}

            await self._make_api_request(
                thread_url,
                method=RequestMethod.POST,
                params=thread_params,
                json_data=thread_data,
            )
        except Exception as e:
            logger.warning(f'Failed to request review from {reviewer}: {e}')

    def send_comment_msg(self, issue_number: int, msg: str) -> None:
        """Send a comment message to an Azure DevOps issue or pull request."""
        asyncio.run(self._send_comment_msg_async(issue_number, msg))

    async def _send_comment_msg_async(self, issue_number: int, msg: str) -> None:
        """Send a comment message to an Azure DevOps issue or pull request asynchronously."""
        try:
            # Add the comment to the work item
            comment_url = f'{self.api_base_url}/wit/workItems/{issue_number}/comments'
            comment_params = {'api-version': '7.1-preview.3'}
            comment_data = {'text': msg}

            await self._make_api_request(
                comment_url,
                method=RequestMethod.POST,
                params=comment_params,
                json_data=comment_data,
            )
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
        """Get context from external issue references."""
        # This method can remain largely the same as it doesn't use Azure DevOps SDK
        context_items = []
        if closing_issues:
            context_items.append(f'Closing issues: {", ".join(closing_issues)}')
        if closing_issue_numbers:
            context_items.append(
                f'Closing issue numbers: {", ".join(map(str, closing_issue_numbers))}'
            )
        if issue_body:
            context_items.append(f'Issue body: {issue_body}')
        if review_comments:
            context_items.extend(review_comments)
        if review_threads:
            for thread in review_threads:
                context_items.append(f'Review thread: {thread.comment}')
        if thread_comments:
            context_items.extend(thread_comments)
        return context_items


class AzureDevOpsPRHandler(AzureDevOpsIssueHandler):
    """Azure DevOps Pull Request handler that extends the issue handler."""

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
        """Download pull requests from Azure DevOps."""
        return asyncio.run(self._download_pull_requests_async())

    async def _download_pull_requests_async(self) -> list[Any]:
        """Download pull requests from Azure DevOps asynchronously."""
        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return []

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return []

            repo_id = repo.get('id')

            # Get all active pull requests for the repository
            prs_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullrequests'
            prs_params = {
                'api-version': '7.1-preview.1',
                'searchCriteria.status': 'active',
            }

            prs_data = await self._make_api_request(prs_url, params=prs_params)

            if not prs_data or not isinstance(prs_data, dict):
                return []

            pull_requests = prs_data.get('value', [])

            # Convert pull requests to the issue format
            all_issues = []
            for pr in pull_requests:
                # Convert the PR to a dictionary format similar to issues
                issue = {
                    'id': pr.get('pullRequestId'),
                    'fields': {
                        'System.Id': pr.get('pullRequestId'),
                        'System.Title': pr.get('title', ''),
                        'System.Description': pr.get('description', ''),
                    },
                    'source_branch': pr.get('sourceRefName', ''),
                    'repository': repo,
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
        """Get metadata for a pull request."""
        return asyncio.run(self._download_pr_metadata_async(pull_number, comment_id))

    async def _download_pr_metadata_async(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str] | None, list[ReviewThread], list[str]]:
        """Get metadata for a pull request asynchronously.

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
        try:
            # First, get the repository ID
            repos_url = f'{self.api_base_url}/git/repositories'
            repos_params = {
                'api-version': '7.1-preview.1',
                'project': self.project_name,
            }

            repos_data = await self._make_api_request(repos_url, params=repos_params)

            if not repos_data or not isinstance(repos_data, dict):
                logger.warning(f'Repository not found: {self.repo_name}')
                return [], [], None, [], []

            repositories = repos_data.get('value', [])
            repo = next(
                (
                    r
                    for r in repositories
                    if r.get('name', '').lower() == self.repo_name.lower()
                ),
                None,
            )

            if not repo:
                logger.warning(f'Repository not found: {self.repo_name}')
                return [], [], None, [], []

            repo_id = repo.get('id')

            # Get the pull request details
            pr_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullRequests/{pull_number}'
            pr_params = {'api-version': '7.1-preview.1'}

            pr_data = await self._make_api_request(pr_url, params=pr_params)

            if not pr_data:
                logger.warning(f'Pull request {pull_number} not found')
                return [], [], None, [], []

            # Get threads (comments) for the pull request
            threads_url = f'{self.api_base_url}/git/repositories/{repo_id}/pullRequests/{pull_number}/threads'
            threads_params = {'api-version': '7.1-preview.1'}

            threads_data = await self._make_api_request(
                threads_url, params=threads_params
            )

            review_threads = []
            thread_ids = []
            review_bodies = []

            if threads_data and isinstance(threads_data, dict):
                threads = threads_data.get('value', [])

                for thread in threads:
                    thread_id = str(thread.get('id', ''))
                    thread_ids.append(thread_id)

                    comments = thread.get('comments', [])
                    if comments:
                        # Get the first comment as the main review body
                        first_comment = comments[0]
                        content = first_comment.get('content', '')
                        if content:
                            review_bodies.append(content)

                        # Create review thread
                        review_thread = ReviewThread(
                            id=thread_id,
                            body=content,
                            line=None,  # Azure DevOps doesn't provide line numbers in the same way
                            start_line=None,
                            original_line=None,
                            original_start_line=None,
                            diff_hunk='',  # Would need additional API call to get diff
                            path='',  # Would need additional API call to get file path
                        )
                        review_threads.append(review_thread)

            # For now, we don't extract closing issues from PR description
            # This would require parsing the description text
            closing_issues: list[str] = []
            closing_issue_numbers: list[int] = []

            return (
                closing_issues,
                closing_issue_numbers,
                review_bodies if review_bodies else None,
                review_threads,
                thread_ids,
            )

        except Exception as e:
            logger.warning(f'Error downloading PR metadata: {e}')
            return [], [], None, [], []
