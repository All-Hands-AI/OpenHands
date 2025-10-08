


"""Pull requests mixin for AWS CodeCommit service."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from botocore.exceptions import ClientError

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import PullRequest, PullRequestComment


class CodeCommitPRsMixin:
    """Pull requests mixin for AWS CodeCommit service."""

    async def get_pull_requests(
        self,
        repository: str,
        state: Literal['open', 'closed', 'all'] = 'open',
        sort: Literal['created', 'updated'] = 'created',
        direction: Literal['asc', 'desc'] = 'desc',
        per_page: int = 100,
    ) -> list[PullRequest]:
        """Get a list of pull requests.

        Args:
            repository: Repository name
            state: Pull request state
            sort: Sort field
            direction: Sort direction
            per_page: Number of pull requests per page

        Returns:
            List of pull requests
        """
        try:
            # Map state to CodeCommit pull request status
            status_map = {
                'open': ['OPEN'],
                'closed': ['CLOSED', 'MERGED'],
                'all': ['OPEN', 'CLOSED', 'MERGED'],
            }
            
            # List pull requests
            response = self.client.list_pull_requests(
                repositoryName=repository,
                pullRequestStatus=status_map[state][0] if len(status_map[state]) == 1 else None,
                # No pagination parameters in boto3 for this call
            )
            
            pull_requests = []
            for pr_id in response.get('pullRequestIds', []):
                try:
                    # Get pull request details
                    pr_info = self.client.get_pull_request(
                        pullRequestId=pr_id
                    )['pullRequest']
                    
                    # Skip if status doesn't match when 'all' is specified
                    if state == 'all' or pr_info['pullRequestStatus'] in status_map[state]:
                        # Create PullRequest object
                        pull_requests.append(
                            PullRequest(
                                id=pr_id,
                                number=int(pr_id.split('-')[-1]) if '-' in pr_id else 0,  # Extract number from ID if possible
                                title=pr_info['title'],
                                body=pr_info.get('description', ''),
                                state=pr_info['pullRequestStatus'].lower(),
                                created_at=pr_info['creationDate'].isoformat() if 'creationDate' in pr_info else None,
                                updated_at=pr_info.get('lastActivityDate', datetime.now()).isoformat() if 'lastActivityDate' in pr_info else None,
                                closed_at=pr_info.get('closedDate', '').isoformat() if 'closedDate' in pr_info else None,
                                merged_at=pr_info.get('mergedDate', '').isoformat() if 'mergedDate' in pr_info else None,
                                head=pr_info['pullRequestTargets'][0]['sourceReference'],
                                base=pr_info['pullRequestTargets'][0]['destinationReference'],
                                user={
                                    'login': pr_info.get('authorArn', '').split('/')[-1],
                                    'id': pr_info.get('authorArn', ''),
                                },
                                assignees=[],  # CodeCommit doesn't have assignees
                                requested_reviewers=[],  # CodeCommit doesn't have requested reviewers
                                labels=[],  # CodeCommit doesn't have labels
                                draft=False,  # CodeCommit doesn't have draft PRs
                            )
                        )
                except ClientError as e:
                    logger.error(f"Failed to get pull request details for {pr_id}: {e}")
                    continue
            
            # Sort pull requests
            if sort == 'created':
                pull_requests.sort(
                    key=lambda pr: pr.created_at if pr.created_at else '',
                    reverse=direction == 'desc'
                )
            elif sort == 'updated':
                pull_requests.sort(
                    key=lambda pr: pr.updated_at if pr.updated_at else '',
                    reverse=direction == 'desc'
                )
                
            return pull_requests[:per_page]
            
        except ClientError as e:
            logger.error(f"Failed to list pull requests for repository {repository}: {e}")
            raise

    async def get_pull_request(self, repository: str, pull_number: int | str) -> PullRequest:
        """Get a pull request.

        Args:
            repository: Repository name
            pull_number: Pull request number or ID

        Returns:
            Pull request
        """
        try:
            # Get pull request details
            pr_info = self.client.get_pull_request(
                pullRequestId=str(pull_number)
            )['pullRequest']
            
            # Create PullRequest object
            return PullRequest(
                id=str(pull_number),
                number=int(str(pull_number).split('-')[-1]) if '-' in str(pull_number) else int(pull_number),
                title=pr_info['title'],
                body=pr_info.get('description', ''),
                state=pr_info['pullRequestStatus'].lower(),
                created_at=pr_info['creationDate'].isoformat() if 'creationDate' in pr_info else None,
                updated_at=pr_info.get('lastActivityDate', datetime.now()).isoformat() if 'lastActivityDate' in pr_info else None,
                closed_at=pr_info.get('closedDate', '').isoformat() if 'closedDate' in pr_info else None,
                merged_at=pr_info.get('mergedDate', '').isoformat() if 'mergedDate' in pr_info else None,
                head=pr_info['pullRequestTargets'][0]['sourceReference'],
                base=pr_info['pullRequestTargets'][0]['destinationReference'],
                user={
                    'login': pr_info.get('authorArn', '').split('/')[-1],
                    'id': pr_info.get('authorArn', ''),
                },
                assignees=[],  # CodeCommit doesn't have assignees
                requested_reviewers=[],  # CodeCommit doesn't have requested reviewers
                labels=[],  # CodeCommit doesn't have labels
                draft=False,  # CodeCommit doesn't have draft PRs
            )
            
        except ClientError as e:
            logger.error(f"Failed to get pull request {pull_number} for repository {repository}: {e}")
            raise

    async def create_pull_request(
        self,
        repository: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False,
    ) -> PullRequest:
        """Create a pull request.

        Args:
            repository: Repository name
            title: Pull request title
            body: Pull request body
            head: Head branch
            base: Base branch
            draft: Whether the pull request is a draft

        Returns:
            Pull request
        """
        try:
            # Create pull request
            response = self.client.create_pull_request(
                title=title,
                description=body,
                targets=[
                    {
                        'repositoryName': repository,
                        'sourceReference': head,
                        'destinationReference': base,
                    }
                ],
                # No draft option in CodeCommit
            )
            
            # Get the created pull request
            pr_id = response['pullRequest']['pullRequestId']
            return await self.get_pull_request(repository, pr_id)
            
        except ClientError as e:
            logger.error(f"Failed to create pull request for repository {repository}: {e}")
            raise

    async def update_pull_request(
        self,
        repository: str,
        pull_number: int | str,
        title: str | None = None,
        body: str | None = None,
        state: Literal['open', 'closed'] | None = None,
    ) -> PullRequest:
        """Update a pull request.

        Args:
            repository: Repository name
            pull_number: Pull request number
            title: Pull request title
            body: Pull request body
            state: Pull request state

        Returns:
            Pull request
        """
        try:
            # Update pull request
            update_params = {}
            
            if title is not None:
                update_params['title'] = title
                
            if body is not None:
                update_params['description'] = body
                
            if update_params:
                self.client.update_pull_request_description(
                    pullRequestId=str(pull_number),
                    description=body
                )
                
                if 'title' in update_params:
                    self.client.update_pull_request_title(
                        pullRequestId=str(pull_number),
                        title=title
                    )
            
            # Handle state change
            if state == 'closed':
                self.client.update_pull_request_status(
                    pullRequestId=str(pull_number),
                    pullRequestStatus='CLOSED'
                )
            
            # Get the updated pull request
            return await self.get_pull_request(repository, pull_number)
            
        except ClientError as e:
            logger.error(f"Failed to update pull request {pull_number} for repository {repository}: {e}")
            raise

    async def merge_pull_request(
        self,
        repository: str,
        pull_number: int | str,
        merge_method: Literal['merge', 'squash', 'rebase'] = 'merge',
    ) -> dict[str, Any]:
        """Merge a pull request.

        Args:
            repository: Repository name
            pull_number: Pull request number
            merge_method: Merge method

        Returns:
            Merge result
        """
        try:
            # Get pull request details
            pr_info = self.client.get_pull_request(
                pullRequestId=str(pull_number)
            )['pullRequest']
            
            # Merge pull request
            # CodeCommit doesn't support different merge methods
            response = self.client.merge_pull_request_by_fast_forward(
                pullRequestId=str(pull_number),
                repositoryName=repository,
                sourceCommitId=pr_info['pullRequestTargets'][0]['sourceCommit']
            )
            
            return {
                'merged': True,
                'message': 'Pull request merged successfully',
                'sha': response.get('pullRequest', {}).get('mergeMetadata', {}).get('mergeCommitId', ''),
            }
            
        except ClientError as e:
            logger.error(f"Failed to merge pull request {pull_number} for repository {repository}: {e}")
            raise

    async def get_pull_request_comments(
        self, repository: str, pull_number: int | str
    ) -> list[PullRequestComment]:
        """Get comments on a pull request.

        Args:
            repository: Repository name
            pull_number: Pull request number

        Returns:
            List of comments
        """
        try:
            # Get pull request comments
            response = self.client.get_comments_for_pull_request(
                pullRequestId=str(pull_number),
                repositoryName=repository
            )
            
            comments = []
            for comment_info in response.get('commentsForPullRequestData', []):
                # Create PullRequestComment object
                comments.append(
                    PullRequestComment(
                        id=comment_info['commentId'],
                        body=comment_info.get('content', ''),
                        created_at=comment_info.get('creationDate', '').isoformat() if comment_info.get('creationDate') else None,
                        updated_at=comment_info.get('lastModifiedDate', '').isoformat() if comment_info.get('lastModifiedDate') else None,
                        user={
                            'login': comment_info.get('authorArn', '').split('/')[-1],
                            'id': comment_info.get('authorArn', ''),
                        },
                    )
                )
                
            return comments
            
        except ClientError as e:
            logger.error(f"Failed to get comments for pull request {pull_number} in repository {repository}: {e}")
            raise

    async def create_pull_request_comment(
        self, repository: str, pull_number: int | str, body: str
    ) -> PullRequestComment:
        """Create a comment on a pull request.

        Args:
            repository: Repository name
            pull_number: Pull request number
            body: Comment body

        Returns:
            Comment
        """
        try:
            # Create pull request comment
            response = self.client.post_comment_for_pull_request(
                pullRequestId=str(pull_number),
                repositoryName=repository,
                content=body,
                clientRequestToken=f"openhands-{datetime.now().timestamp()}"
            )
            
            comment_info = response['comment']
            
            # Create PullRequestComment object
            return PullRequestComment(
                id=comment_info['commentId'],
                body=comment_info.get('content', ''),
                created_at=comment_info.get('creationDate', '').isoformat() if comment_info.get('creationDate') else None,
                updated_at=comment_info.get('lastModifiedDate', '').isoformat() if comment_info.get('lastModifiedDate') else None,
                user={
                    'login': comment_info.get('authorArn', '').split('/')[-1],
                    'id': comment_info.get('authorArn', ''),
                },
            )
            
        except ClientError as e:
            logger.error(f"Failed to create comment for pull request {pull_number} in repository {repository}: {e}")
            raise

    async def get_issue_comments(
        self, repository: str, issue_number: int | str
    ) -> list[PullRequestComment]:
        """Get comments on an issue.

        Args:
            repository: Repository name
            issue_number: Issue number

        Returns:
            List of comments
        """
        # CodeCommit doesn't have separate issues, only pull requests
        # Redirect to get_pull_request_comments
        return await self.get_pull_request_comments(repository, issue_number)

    async def create_issue_comment(
        self, repository: str, issue_number: int | str, body: str
    ) -> PullRequestComment:
        """Create a comment on an issue.

        Args:
            repository: Repository name
            issue_number: Issue number
            body: Comment body

        Returns:
            Comment
        """
        # CodeCommit doesn't have separate issues, only pull requests
        # Redirect to create_pull_request_comment
        return await self.create_pull_request_comment(repository, issue_number, body)


