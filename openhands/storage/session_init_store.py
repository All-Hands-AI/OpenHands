from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.app_config import AppConfig
from openhands.server.session.session_init_data import SessionInitData


class SessionInitStore(ABC):
    """
    Storage for SessionInitData. May or may not support multiple users depending on the environment
    """

    @abstractmethod
    def load(self) -> SessionInitData | None:
        """Load session init data"""

    @abstractmethod
    def store(self, session_init_data: SessionInitData):
        """Store session init data"""

    @classmethod
    @abstractmethod
    def get_instance(cls, config: AppConfig, token: str | None) -> SessionInitStore:
        """Get a store for the user represented by the token given"""
