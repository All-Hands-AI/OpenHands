from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import sessionmaker
from storage.database import session_maker
from storage.stored_offline_token import StoredOfflineToken

from openhands.core.config.openhands_config import OpenHandsConfig
from openhands.core.logger import openhands_logger as logger


@dataclass
class OfflineTokenStore:
    user_id: str
    session_maker: sessionmaker
    config: OpenHandsConfig

    async def store_token(self, offline_token: str) -> None:
        """Store an offline token in the database."""
        with self.session_maker() as session:
            token_record = (
                session.query(StoredOfflineToken)
                .filter(StoredOfflineToken.user_id == self.user_id)
                .first()
            )

            if token_record:
                token_record.offline_token = offline_token
            else:
                token_record = StoredOfflineToken(
                    user_id=self.user_id, offline_token=offline_token
                )
                session.add(token_record)
            session.commit()

    async def load_token(self) -> str | None:
        """Load an offline token from the database."""
        with self.session_maker() as session:
            token_record = (
                session.query(StoredOfflineToken)
                .filter(StoredOfflineToken.user_id == self.user_id)
                .first()
            )

            if not token_record:
                return None

            return token_record.offline_token

    @classmethod
    async def get_instance(
        cls, config: OpenHandsConfig, user_id: str
    ) -> OfflineTokenStore:
        """Get an instance of the OfflineTokenStore."""
        logger.debug(f'offline_token_store.get_instance::{user_id}')
        if user_id:
            user_id = str(user_id)
        return OfflineTokenStore(user_id, session_maker, config)
