

"""Branches mixin for AWS CodeCommit service."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import Branch


class CodeCommitBranchesMixin:
    """Branches mixin for AWS CodeCommit service."""

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get a list of branches for a repository.

        Args:
            repository: Repository name

        Returns:
            List of branches
        """
        try:
            # List branches
            response = self.client.list_branches(
                repositoryName=repository
            )
            
            branches = []
            for branch_name in response.get('branches', []):
                try:
                    # Get branch details
                    branch_info = self.client.get_branch(
                        repositoryName=repository,
                        branchName=branch_name
                    )['branch']
                    
                    # Create Branch object
                    branches.append(
                        Branch(
                            name=branch_name,
                            commit=branch_info['commitId'],
                            protected=False,  # CodeCommit doesn't have branch protection in the same way
                        )
                    )
                except ClientError as e:
                    logger.error(f"Failed to get branch details for {branch_name}: {e}")
                    continue
                    
            return branches
            
        except ClientError as e:
            logger.error(f"Failed to list branches for repository {repository}: {e}")
            raise

    async def get_branch(self, repository: str, branch: str) -> Branch:
        """Get a branch.

        Args:
            repository: Repository name
            branch: Branch name

        Returns:
            Branch
        """
        try:
            # Get branch details
            branch_info = self.client.get_branch(
                repositoryName=repository,
                branchName=branch
            )['branch']
            
            # Create Branch object
            return Branch(
                name=branch,
                commit=branch_info['commitId'],
                protected=False,  # CodeCommit doesn't have branch protection in the same way
            )
            
        except ClientError as e:
            logger.error(f"Failed to get branch {branch} for repository {repository}: {e}")
            raise

    async def create_branch(
        self, repository: str, branch: str, source_branch: str
    ) -> Branch:
        """Create a branch.

        Args:
            repository: Repository name
            branch: Branch name
            source_branch: Source branch name

        Returns:
            Branch
        """
        try:
            # Get the commit ID of the source branch
            source_branch_info = self.client.get_branch(
                repositoryName=repository,
                branchName=source_branch
            )['branch']
            
            source_commit_id = source_branch_info['commitId']
            
            # Create the branch
            self.client.create_branch(
                repositoryName=repository,
                branchName=branch,
                commitId=source_commit_id
            )
            
            # Return the new branch
            return Branch(
                name=branch,
                commit=source_commit_id,
                protected=False,
            )
            
        except ClientError as e:
            logger.error(f"Failed to create branch {branch} for repository {repository}: {e}")
            raise

    async def get_branch_protection(self, repository: str, branch: str) -> dict[str, Any]:
        """Get branch protection settings.

        Args:
            repository: Repository name
            branch: Branch name

        Returns:
            Branch protection settings
        """
        # CodeCommit doesn't have branch protection in the same way as GitHub or GitLab
        # Return an empty dictionary
        return {}

