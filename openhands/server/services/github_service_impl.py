from typing import Optional

from openhands.server.services.github_service import GitHubService


class GithubServiceImpl:
    _instance: Optional[GitHubService] = None

    @classmethod
    def get_instance(cls, user_id: str | None = None) -> GitHubService:
        if not cls._instance:
            cls._instance = GitHubService(user_id)
        return cls._instance