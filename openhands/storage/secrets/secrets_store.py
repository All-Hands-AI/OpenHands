from __future__ import annotations

from abc import ABC, abstractmethod

from openhands.core.config.app_config import AppConfig
from openhands.storage.data_models.user_secrets import UserSecrets


class SecretsStore(ABC):
    """Storage for secrets. May or may not support multiple users depending on the environment."""

    @abstractmethod
    async def load(self) -> UserSecrets | None:
        """Load secrets."""

    @abstractmethod
    async def store(self, secrets: UserSecrets) -> None:
        """Store secrets."""

    @classmethod
    @abstractmethod
    async def get_instance(cls, config: AppConfig, user_id: str | None) -> SecretsStore:
        """Get a store for the user represented by the token given."""
