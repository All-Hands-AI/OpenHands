import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, List

from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.service_types import (
    BaseGitService,
    Branch,
    GitService,
    ProviderType,
    Repository,
    RequestMethod,
    SuggestedTask,
    User,
)
from openhands.server.types import AppMode
from openhands.utils.import_utils import get_impl


class LocalGitService(BaseGitService, GitService):
    """Service for interacting with local git repositories."""

    def __init__(
        self,
        user_id: str | None = None,
        external_auth_id: str | None = None,
        external_auth_token: SecretStr | None = None,
        token: SecretStr | None = None,
        external_token_manager: bool = False,
        base_domain: str | None = None,
    ):
        self.user_id = user_id
        self.external_token_manager = external_token_manager
        self.external_auth_id = external_auth_id
        self.external_auth_token = external_auth_token
        self.token = token or SecretStr("")

    @property
    def provider(self) -> str:
        return ProviderType.LOCAL.value

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:
        """
        Not used for local git service, but required by the BaseGitService interface.
        """
        return {}, {}

    async def get_latest_token(self) -> SecretStr | None:
        """Get latest working token of the user"""
        return self.token

    async def get_user(self) -> User:
        """Get the authenticated user's information"""
        # For local git, we use a placeholder user
        return User(
            id=0,
            login="local-user",
            avatar_url="",
            company=None,
            name="Local Git User",
            email=None,
        )

    def _find_git_repositories(self, base_dir: str) -> List[Repository]:
        """
        Find git repositories in the given directory and one level deep.
        
        Args:
            base_dir: The base directory to search for git repositories
            
        Returns:
            A list of Repository objects for git repositories found
        """
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            logger.warning(f"WORKSPACE_BASE directory does not exist or is not a directory: {base_dir}")
            return []
            
        repositories = []
        base_path = Path(base_dir)
        
        # Check if the base directory itself is a git repository
        if (base_path / '.git').is_dir():
            repo = self._create_repository_from_local_git(base_path)
            if repo:
                repositories.append(repo)
                
        # Check one level deep
        for item in base_path.iterdir():
            if item.is_dir():
                # Check if this directory is a git repository
                if (item / '.git').is_dir():
                    repo = self._create_repository_from_local_git(item)
                    if repo:
                        repositories.append(repo)
                        
        return repositories
        
    def _create_repository_from_local_git(self, repo_path: Path) -> Repository | None:
        """
        Create a Repository object from a local git repository.
        
        Args:
            repo_path: Path to the git repository
            
        Returns:
            A Repository object or None if the repository information cannot be extracted
        """
        try:
            # Get repository name from directory name
            repo_name = repo_path.name
            
            # Try to get the remote URL to extract the full name
            try:
                result = subprocess.run(
                    ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                remote_url = result.stdout.strip()
                
                # Extract full name from remote URL if possible
                if remote_url:
                    # Handle different URL formats
                    if remote_url.startswith("https://"):
                        # Format: https://github.com/username/repo.git
                        parts = remote_url.split("/")
                        if len(parts) >= 5:
                            owner = parts[-2]
                            repo = parts[-1]
                            if repo.endswith(".git"):
                                repo = repo[:-4]
                            full_name = f"{owner}/{repo}"
                        else:
                            full_name = f"local/{repo_name}"
                    elif remote_url.startswith("git@"):
                        # Format: git@github.com:username/repo.git
                        parts = remote_url.split(":")
                        if len(parts) == 2:
                            repo_part = parts[1]
                            if repo_part.endswith(".git"):
                                repo_part = repo_part[:-4]
                            full_name = repo_part
                        else:
                            full_name = f"local/{repo_name}"
                    else:
                        full_name = f"local/{repo_name}"
                else:
                    full_name = f"local/{repo_name}"
                    
            except Exception as e:
                logger.warning(f"Error getting remote URL for repository {repo_path}: {e}")
                full_name = f"local/{repo_name}"
                
            # Create a unique ID for the repository
            repo_id = hash(str(repo_path.absolute()))
            
            # Get last commit date if available
            pushed_at = None
            try:
                result = subprocess.run(
                    ["git", "-C", str(repo_path), "log", "-1", "--format=%cI"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.stdout.strip():
                    pushed_at = result.stdout.strip()
            except Exception:
                pass
                
            # Create the Repository object
            return Repository(
                id=abs(repo_id),  # Use absolute value to ensure positive ID
                full_name=full_name,
                git_provider=ProviderType.LOCAL,
                is_public=False,  # Assume local repositories are private
                stargazers_count=0,
                pushed_at=pushed_at,
            )
            
        except Exception as e:
            logger.warning(f"Error creating repository object for {repo_path}: {e}")
            return None

    async def search_repositories(
        self, query: str, per_page: int, sort: str, order: str
    ) -> list[Repository]:
        """Search for repositories - not implemented for local git"""
        return []

    async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories from the local workspace"""
        workspace_base = os.environ.get('WORKSPACE_BASE')
        if not workspace_base:
            return []
            
        logger.info(f"Looking for git repositories in WORKSPACE_BASE: {workspace_base}")
        local_repos = self._find_git_repositories(workspace_base)
        if local_repos:
            logger.info(f"Found {len(local_repos)} local git repositories in WORKSPACE_BASE")
            
        return local_repos

    async def get_suggested_tasks(self) -> list[SuggestedTask]:
        """Get suggested tasks - not implemented for local git"""
        return []

    async def get_repository_details_from_repo_name(
        self, repository: str
    ) -> Repository:
        """Gets repository details from repository name - not fully implemented for local git"""
        # This is a simplified implementation that just returns a basic Repository object
        return Repository(
            id=hash(repository),
            full_name=repository,
            git_provider=ProviderType.LOCAL,
            is_public=False,
            stargazers_count=0,
        )

    async def get_branches(self, repository: str) -> list[Branch]:
        """Get branches for a repository - simplified implementation for local git"""
        # This would need to be expanded to actually find the local repository
        # and extract branch information
        return []


local_git_service_cls = os.environ.get(
    'OPENHANDS_LOCAL_GIT_SERVICE_CLS',
    'openhands.integrations.local.local_git_service.LocalGitService',
)
LocalGitServiceImpl = get_impl(LocalGitService, local_git_service_cls)