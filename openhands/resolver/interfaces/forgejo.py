from typing import Any

import httpx

from openhands.core.logger import openhands_logger as logger
from openhands.resolver.interfaces.issue import (
    Issue,
    IssueHandlerInterface,
    ReviewThread,
)
from openhands.resolver.utils import extract_issue_references


class ForgejoIssueHandler(IssueHandlerInterface):
    def __init__(self, owner: str, repo: str, token: str, username: str | None = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.username = username
        self.base_url = self.get_base_url()
        self.download_url = self.get_download_url()
        self.clone_url = self.get_clone_url()
        self.headers = self.get_headers()

    def set_owner(self, owner: str) -> None:
        self.owner = owner

    def get_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/json',
        }

    def get_base_url(self) -> str:
        return f'https://codeberg.org/api/v1/repos/{self.owner}/{self.repo}'

    def get_authorize_url(self) -> str:
        return f'https://{self.username}:{self.token}@codeberg.org/'

    def get_branch_url(self, branch_name: str) -> str:
        return self.get_base_url() + f'/branches/{branch_name}'

    def get_download_url(self) -> str:
        return f'{self.base_url}/issues'

    def get_clone_url(self) -> str:
        username_and_token = (
            f'{self.username}:{self.token}'
            if self.username
            else f'x-auth-token:{self.token}'
        )
        return f'https://{username_and_token}@codeberg.org/{self.owner}/{self.repo}.git'

    def get_compare_url(self, branch_name: str) -> str:
        return f'https://codeberg.org/{self.owner}/{self.repo}/compare/{branch_name}?expand=1'

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Forgejo.

        Args:
            issue_numbers: The numbers of the issues to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Forgejo issues.
        """

        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [
            issue
            for issue in all_issues
            if issue['number'] in issue_numbers and not issue.get('pull_request')
        ]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            # Check for required fields (number and title)
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(
                    f'Skipping issue {issue} as it is missing number or title.'
                )
                continue

            # Handle empty body by using empty string
            if issue.get('body') is None:
                issue['body'] = ''

            # Get issue thread comments
            thread_comments = self.get_issue_comments(
                issue['number'], comment_id=comment_id
            )
            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['number'],
                title=issue['title'],
                body=issue['body'],
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues

    def download_issues(self) -> list[Any]:
        params: dict[str, int | str] = {'state': 'open', 'page': 1, 'limit': 100}
        all_issues = []

        while True:
            response = httpx.get(self.download_url, headers=self.headers, params=params)
            response.raise_for_status()
            issues = response.json()

            if not issues:
                break

            if not isinstance(issues, list) or any(
                [not isinstance(issue, dict) for issue in issues]
            ):
                raise ValueError(
                    'Expected list of dictionaries from Service Forgejo API.'
                )

            all_issues.extend(issues)
            assert isinstance(params['page'], int)
            params['page'] += 1

        return all_issues

    def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific issue from Forgejo."""
        url = f'{self.download_url}/{issue_number}/comments'
        params = {'page': 1, 'limit': 100}
        all_comments = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            if comment_id:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if comment['id'] == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments.extend([comment['body'] for comment in comments])

            params['page'] += 1

        return all_comments if all_comments else None

    def branch_exists(self, branch_name: str) -> bool:
        logger.info(f'Checking if branch {branch_name} exists...')
        response = httpx.get(
            f'{self.base_url}/branches/{branch_name}', headers=self.headers
        )
        exists = response.status_code == 200
        logger.info(f'Branch {branch_name} exists: {exists}')
        return exists

    def get_branch_name(self, base_branch_name: str) -> str:
        branch_name = base_branch_name
        attempt = 1
        while self.branch_exists(branch_name):
            attempt += 1
            branch_name = f'{base_branch_name}-try{attempt}'
        return branch_name

    def reply_to_comment(self, pr_number: int, comment_id: str, reply: str) -> None:
        """Reply to a specific comment on a pull request.

        Forgejo doesn't have a direct API endpoint for replying to specific comments
        like GitHub does. While the internal data model supports reference comments,
        there's no exposed API for this functionality.

        As a workaround, we'll add a new comment that mentions the original comment.
        """
        # Format the reply to reference the original comment
        formatted_reply = f'In response to comment {comment_id}:\n\n{reply}'
        self.send_comment_msg(pr_number, formatted_reply)

    def get_pull_url(self, pr_number: int) -> str:
        return f'https://codeberg.org/{self.owner}/{self.repo}/pulls/{pr_number}'

    def get_default_branch_name(self) -> str:
        response = httpx.get(f'{self.base_url}', headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return str(data['default_branch'])

    def create_pull_request(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if data is None:
            data = {}
        response = httpx.post(f'{self.base_url}/pulls', headers=self.headers, json=data)
        if response.status_code == 403:
            raise RuntimeError(
                'Failed to create pull request due to missing permissions. '
                'Make sure that the provided token has push permissions for the repository.'
            )
        response.raise_for_status()
        pr_data = response.json()
        return dict(pr_data)

    def request_reviewers(self, reviewer: str, pr_number: int) -> None:
        """Request a reviewer for a pull request.

        Forgejo supports requesting reviewers via the API.
        """
        url = f'{self.base_url}/pulls/{pr_number}/requested_reviewers'

        # The API expects a PullReviewRequestOptions object with reviewers as a list of strings
        data = {'reviewers': [reviewer], 'team_reviewers': []}

        response = httpx.post(url, headers=self.headers, json=data)

        if response.status_code not in (200, 201):
            logger.warning(f'Failed to request review from {reviewer}: {response.text}')
            # Fallback to mentioning the reviewer in a comment
            msg = f'@{reviewer} Could you please review this pull request?'
            self.send_comment_msg(pr_number, msg)

    def get_review_comments(self, pr_number: int) -> list[dict[str, Any]]:
        """Get review comments for a pull request.

        Args:
            pr_number: The pull request number

        Returns:
            List of review comments
        """
        url = f'{self.base_url}/pulls/{pr_number}/comments'
        params = {'page': 1, 'limit': 100}
        all_comments = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            all_comments.extend(comments)
            params['page'] += 1

        return all_comments
        
    def get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific pull request from Forgejo.
        
        Args:
            pr_number: The pull request number
            comment_id: Optional ID of a specific comment to focus on
            
        Returns:
            List of comment bodies or None if no comments
        """
        url = f'{self.base_url}/issues/{pr_number}/comments'
        params = {'page': 1, 'limit': 100}
        all_comments = []
        
        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()
            
            if not comments:
                break
                
            if comment_id:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if comment['id'] == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments.extend([comment['body'] for comment in comments])
                
            params['page'] += 1
            
        return all_comments if all_comments else None

    def get_review_threads(self, pr_number: int) -> list[dict[str, Any]]:
        """Get review threads for a pull request.

        Forgejo organizes code comments into "CodeConversations" which are collections
        of comments on the same line of code from the same review. However, the API
        doesn't expose these conversations directly in the same way GitHub does.

        This implementation creates synthetic "threads" by grouping comments by their
        file path and line number, which approximates how Forgejo would display them
        in the UI.
        """
        comments = self.get_review_comments(pr_number)

        # Group comments by path and line to simulate Forgejo's CodeConversations
        conversations = {}  # path -> line -> [comments]

        for comment in comments:
            path = comment.get('path', '')
            line = comment.get('position', 0)
            review_id = comment.get('pull_request_review_id', 0)
            key = f'{path}:{line}:{review_id}'

            if key not in conversations:
                conversations[key] = {
                    'path': path,
                    'line': line,
                    'position': line,
                    'review_id': review_id,
                    'comments': [],
                }

            conversations[key]['comments'].append(comment)

        # Convert the grouped conversations to threads
        threads = []
        for key, conversation in conversations.items():
            # Use the ID of the first comment as the thread ID
            thread_id = (
                conversation['comments'][0]['id'] if conversation['comments'] else 0
            )

            thread = {
                'id': thread_id,
                'comments': conversation['comments'],
                'path': conversation['path'],
                'line': conversation['line'],
                'position': conversation['position'],
                'review_id': conversation['review_id'],
            }
            threads.append(thread)

        return threads

    def send_comment_msg(self, issue_number: int, msg: str) -> None:
        """Send a comment message to a Forgejo issue or pull request.

        Args:
            issue_number: The issue or pull request number
            msg: The message content to post as a comment
        """
        # Post a comment on the PR
        comment_url = f'{self.base_url}/issues/{issue_number}/comments'
        comment_data = {'body': msg}
        comment_response = httpx.post(
            comment_url, headers=self.headers, json=comment_data
        )
        if comment_response.status_code != 201:
            logger.error(
                f'Failed to post comment: {comment_response.status_code} {comment_response.text}'
            )
        else:
            logger.info(f'Comment added to the PR: {msg}')

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


class ForgejoPRHandler(ForgejoIssueHandler):
    def __init__(self, owner: str, repo: str, token: str, username: str | None = None):
        super().__init__(owner, repo, token, username)
        self.download_url = (
            f'https://codeberg.org/api/v1/repos/{self.owner}/{self.repo}/pulls'
        )

    def download_pr_metadata(
        self, pull_number: int, comment_id: int | None = None
    ) -> tuple[list[str], list[int], list[str], list[ReviewThread], list[str]]:
        """Get metadata for a pull request.

        Args:
            pull_number: The number of the pull request to query.
            comment_id: Optional ID of a specific comment to focus on.

        Returns:
            Tuple containing:
            - List of closing issue bodies
            - List of closing issue numbers
            - List of review bodies
            - List of review threads
            - List of thread comments
        """
        # Get the PR details
        pr_url = f'{self.base_url}/pulls/{pull_number}'
        pr_response = httpx.get(pr_url, headers=self.headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get closing issues from PR body
        closing_issues_bodies = []
        closing_issue_numbers = []
        if pr_data.get('body'):
            # Extract issue references from PR body
            issue_refs = extract_issue_references(pr_data['body'])
            for issue_ref in issue_refs:
                try:
                    issue_url = f'{self.base_url}/issues/{issue_ref}'
                    issue_response = httpx.get(issue_url, headers=self.headers)
                    if issue_response.status_code == 200:
                        issue_data = issue_response.json()
                        closing_issues_bodies.append(issue_data.get('body', ''))
                        closing_issue_numbers.append(issue_data.get('number'))
                except Exception as e:
                    logger.warning(f'Error fetching issue {issue_ref}: {e}')

        # Get review comments
        review_url = f'{self.base_url}/pulls/{pull_number}/comments'
        review_params = {'page': 1, 'limit': 100}
        review_comments = []

        while True:
            review_response = httpx.get(
                review_url, headers=self.headers, params=review_params
            )
            review_response.raise_for_status()
            comments = review_response.json()

            if not comments:
                break

            if comment_id:
                matching_comments = [c for c in comments if c.get('id') == comment_id]
                if matching_comments:
                    review_comments.extend(
                        [c.get('body', '') for c in matching_comments]
                    )
                    break
            else:
                review_comments.extend([c.get('body', '') for c in comments])

            review_params['page'] += 1

        # Get PR comments (thread comments)
        thread_url = f'{self.base_url}/issues/{pull_number}/comments'
        thread_params = {'page': 1, 'limit': 100}
        thread_comments = []

        while True:
            thread_response = httpx.get(
                thread_url, headers=self.headers, params=thread_params
            )
            thread_response.raise_for_status()
            comments = thread_response.json()

            if not comments:
                break

            if comment_id:
                matching_comments = [c for c in comments if c.get('id') == comment_id]
                if matching_comments:
                    thread_comments.extend(
                        [c.get('body', '') for c in matching_comments]
                    )
                    break
            else:
                thread_comments.extend([c.get('body', '') for c in comments])

            thread_params['page'] += 1

        # Create review threads
        # Forgejo organizes code comments into "CodeConversations" which are collections
        # of comments on the same line of code from the same review. However, the API
        # doesn't expose these conversations directly in the same way GitHub does.
        #
        # Since we only have the comment bodies here and not the full comment objects with
        # path and line information, we'll create individual threads for each comment.
        # In a more complete implementation, we would group comments by path and line.
        review_threads = []
        for i, comment in enumerate(review_comments):
            thread = ReviewThread(
                id=str(comment_id) if comment_id else str(i),
                message=comment,
                files=[],
            )
            review_threads.append(thread)

        return (
            closing_issues_bodies,
            closing_issue_numbers,
            review_comments,
            review_threads,
            thread_comments,
        )

    def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download pull requests from Forgejo.

        Args:
            issue_numbers: The numbers of the pull requests to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Forgejo pull requests as Issues.
        """
        if not issue_numbers:
            raise ValueError('Unspecified pull request number')

        all_prs = self.download_prs()
        logger.info(f'Limiting resolving to pull requests {issue_numbers}.')
        all_prs = [pr for pr in all_prs if pr['number'] in issue_numbers]

        if len(issue_numbers) == 1 and not all_prs:
            raise ValueError(f'Pull request {issue_numbers[0]} not found')

        converted_issues = []
        for pr in all_prs:
            # Check for required fields (number and title)
            if any([pr.get(key) is None for key in ['number', 'title']]):
                logger.warning(
                    f'Skipping pull request {pr} as it is missing number or title.'
                )
                continue

            # Handle empty body by using empty string
            if pr.get('body') is None:
                pr['body'] = ''

            # Get PR metadata
            (
                closing_issues,
                closing_issue_numbers,
                review_comments,
                review_threads,
                thread_comments,
            ) = self.download_pr_metadata(pr['number'], comment_id)

            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=pr['number'],
                title=pr['title'],
                body=pr['body'],
                thread_comments=thread_comments if thread_comments else None,
                review_comments=review_comments if review_comments else None,
                review_threads=review_threads if review_threads else None,
                closing_issues=closing_issues if closing_issues else None,
                closing_issue_numbers=closing_issue_numbers
                if closing_issue_numbers
                else None,
            )

            converted_issues.append(issue_details)

        return converted_issues

    def download_prs(self) -> list[Any]:
        params: dict[str, int | str] = {'state': 'open', 'page': 1, 'limit': 100}
        all_prs = []

        while True:
            response = httpx.get(self.download_url, headers=self.headers, params=params)
            response.raise_for_status()
            prs = response.json()

            if not prs:
                break

            if not isinstance(prs, list) or any(
                [not isinstance(pr, dict) for pr in prs]
            ):
                raise ValueError(
                    'Expected list of dictionaries from Service Forgejo API.'
                )

            all_prs.extend(prs)
            assert isinstance(params['page'], int)
            params['page'] += 1

        return all_prs
