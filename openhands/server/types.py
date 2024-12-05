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
    ATTACH_SESSION_MIDDLEWARE: ClassVar[type[SessionMiddlewareInterface]]

    @abstractmethod
    def verify_config(self) -> None:
        """Verify configuration settings."""
        raise NotImplementedError

    @abstractmethod
    async def github_auth(self) -> None:
        """Handle GitHub authentication."""
        raise NotImplementedError