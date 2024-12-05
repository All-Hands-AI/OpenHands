import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Protocol

from openhands.server.middleware import AttachSessionMiddleware
from openhands.utils.import_utils import import_from


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


class OpenhandsOssConfig(OpenhandsConfigInterface):
    CONFIG_PATH = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    APP_MODE = AppMode.OSS
    POSTHOG_CLIENT_KEY = 'phc_3ESMmY9SgqEAGBB6sMGK5ayYHkeUuknH2vP6FmWH9RA'
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_APP_CLIENT_ID', '')
    ATTACH_SESSION_MIDDLEWARE = AttachSessionMiddleware

    def verify_config(self):
        if self.CONFIG_PATH:
            raise ValueError('Unexpected config path provided')

    async def github_auth(self):
        """
        Skip Github Auth for AppMode OSS
        """
        pass


def load_openhands_config():
    config_path = os.environ.get('OPENHANDS_CONFIG_PATH', None)
    if config_path:
        OpenhandsConfig = import_from(config_path)
    else:
        OpenhandsConfig = OpenhandsOssConfig()

    OpenhandsConfig.verify_config()

    return OpenhandsConfig
