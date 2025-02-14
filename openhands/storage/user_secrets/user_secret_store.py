from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.app_config import AppConfig
from openhands.storage.data_models.user_secret import UserSecret
from openhands.storage.data_models.user_secret_result_set import UserSecretResultSet


class UserSecretStore(ABC):
    """
    Storage for secrets. In a multi user environment, is limited to the context of a single user.
    """

    @abstractmethod
    async def save_secret(self, secret: UserSecret):
        """Store conversation metadata"""

    @abstractmethod
    async def load_secret(self, id: str) -> UserSecret | None:
        """Load secret"""

    @abstractmethod
    async def delete_secret(self, id: str) -> bool:
        """delete secret"""

    @abstractmethod
    async def search(
        self,
        page_id: str | None = None,
        limit: int = 20,
    ) -> UserSecretResultSet:
        """Search secrets. The ordering of results is undefined."""

    @classmethod
    @abstractmethod
    async def get_instance(
        cls, config: AppConfig, user_id: str | None
    ) -> UserSecretStore:
        """Get a store for the user represented by the token given"""
