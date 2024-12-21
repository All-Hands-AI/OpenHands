from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Protocol


class AppMode(Enum):
    OSS = 'oss'
    SAAS = 'saas'


class SessionMiddlewareInterface(Protocol):
    """Protocol for session middleware classes."""

    pass


class OpenhandsConfigInterface(ABC):
    CONFIG_PATH: ClassVar[str | None]
    APP_MODE: ClassVar[AppMode]
    POSTHOG_CLIENT_KEY: ClassVar[str]
    GITHUB_CLIENT_ID: ClassVar[str]
    ATTACH_SESSION_MIDDLEWARE_PATH: ClassVar[str]

    @abstractmethod
    def verify_config(self) -> None:
        """Verify configuration settings."""
        raise NotImplementedError

    @abstractmethod
    async def verify_github_repo_list(self, installation_id: int | None) -> None:
        """Verify that repo list is being called via user's profile or Github App installations."""
        raise NotImplementedError

    @abstractmethod
    async def get_config(self) -> dict[str, str]:
        """Configure attributes for frontend"""
        raise NotImplementedError
