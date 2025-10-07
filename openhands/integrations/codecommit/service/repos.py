

"""Repositories mixin for AWS CodeCommit service."""

from __future__ import annotations

from typing import Any, Literal

from botocore.exceptions import ClientError

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import Repository


class CodeCommitReposMixin:
    """Repositories mixin for AWS CodeCommit service."""

    async def get_repositories(self, per_page: int = 100) -> list[Repository]:
        """Get a list of repositories.

        Args:
            per_page: Number of repositories per page

        Returns:
            List of repositories
        """
        try:
            # List repositories
            response = self.client.list_repositories(
                sortBy='repositoryName',
                order='ascending',
                # No pagination parameters in boto3 for this call
            )
            
            repositories = []
            for repo in response.get('repositories', []):
                # Get repository details
                try:
                    repo_info = self.client.get_repository(
                        repositoryName=repo['repositoryName']
                    )['repositoryMetadata']
                    
                    # Create Repository object
                    repositories.append(
                        Repository(
                            id=repo_info['repositoryId'],
                            name=repo_info['repositoryName'],
                            full_name=repo_info['repositoryName'],
                            description=repo_info.get('repositoryDescription', ''),
                            url=f"https://git-codecommit.{self.region}.amazonaws.com/v1/repos/{repo_info['repositoryName']}",
                            private=True,  # CodeCommit repositories are always private
                            owner=repo_info.get('accountId', ''),
                            provider='codecommit',
                            default_branch=repo_info.get('defaultBranch', 'main'),
                            created_at=repo_info.get('creationDate', '').isoformat() if repo_info.get('creationDate') else None,
                            updated_at=repo_info.get('lastModifiedDate', '').isoformat() if repo_info.get('lastModifiedDate') else None,
                        )
                    )
                except ClientError as e:
                    logger.error(f"Failed to get repository details for {repo['repositoryName']}: {e}")
                    continue
                    
            return repositories[:per_page]  # Limit to per_page
            
        except ClientError as e:
            logger.error(f"Failed to list repositories: {e}")
            raise

    async def search_repositories(
        self,
        query: str,
        per_page: int = 100,
        sort: str | None = None,
        order: Literal['asc', 'desc'] | None = None,
        public: bool = False,
    ) -> list[Repository]:
        """Search for repositories.

        Args:
            query: Search query
            per_page: Number of repositories per page
            sort: Sort field
            order: Sort order
            public: Whether to search for public repositories

        Returns:
            List of repositories
        """
        try:
            # Get all repositories and filter by name
            repositories = await self.get_repositories(per_page=100)
            
            # Filter repositories by query
            filtered_repos = [
                repo for repo in repositories 
                if query.lower() in repo.name.lower() or 
                   (repo.description and query.lower() in repo.description.lower())
            ]
            
            # Sort repositories if sort field is provided
            if sort and sort == 'updated':
                filtered_repos.sort(
                    key=lambda r: r.updated_at if r.updated_at else '',
                    reverse=order == 'desc'
                )
            elif sort and sort == 'created':
                filtered_repos.sort(
                    key=lambda r: r.created_at if r.created_at else '',
                    reverse=order == 'desc'
                )
            elif sort and sort == 'name':
                filtered_repos.sort(
                    key=lambda r: r.name.lower(),
                    reverse=order == 'desc'
                )
                
            return filtered_repos[:per_page]
            
        except Exception as e:
            logger.error(f"Failed to search repositories: {e}")
            raise

    async def get_repository(self, repository: str) -> Repository:
        """Get a repository.

        Args:
            repository: Repository name

        Returns:
            Repository
        """
        try:
            # Get repository details
            repo_info = self.client.get_repository(
                repositoryName=repository
            )['repositoryMetadata']
            
            # Create Repository object
            return Repository(
                id=repo_info['repositoryId'],
                name=repo_info['repositoryName'],
                full_name=repo_info['repositoryName'],
                description=repo_info.get('repositoryDescription', ''),
                url=f"https://git-codecommit.{self.region}.amazonaws.com/v1/repos/{repo_info['repositoryName']}",
                private=True,  # CodeCommit repositories are always private
                owner=repo_info.get('accountId', ''),
                provider='codecommit',
                default_branch=repo_info.get('defaultBranch', 'main'),
                created_at=repo_info.get('creationDate', '').isoformat() if repo_info.get('creationDate') else None,
                updated_at=repo_info.get('lastModifiedDate', '').isoformat() if repo_info.get('lastModifiedDate') else None,
            )
            
        except ClientError as e:
            logger.error(f"Failed to get repository {repository}: {e}")
            raise

    async def get_repository_languages(self, repository: str) -> dict[str, Any]:
        """Get languages used in a repository.

        Args:
            repository: Repository name

        Returns:
            Dictionary of languages and their usage percentage
        """
        # CodeCommit doesn't provide language statistics
        # Return an empty dictionary
        return {}

