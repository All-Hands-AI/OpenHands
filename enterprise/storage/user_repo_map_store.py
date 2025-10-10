from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from storage.database import session_maker
from storage.user_repo_map import UserRepositoryMap

from openhands.core.config.openhands_config import OpenHandsConfig


@dataclass
class UserRepositoryMapStore:
    session_maker: sessionmaker
    config: OpenHandsConfig

    def store_user_repo_mappings(self, mappings: list[UserRepositoryMap]) -> None:
        """
        Store user-repository mappings in database

        1. Make sure to store mappings if they don't exist
        2. If a mapping already exists (same user_id and repo_id), update the admin field

        This implementation uses batch operations for better performance with large numbers of mappings.

        Args:
            mappings: List of UserRepositoryMap objects to store
        """
        if not mappings:
            return

        with self.session_maker() as session:
            # Extract all user_id/repo_id pairs to check
            mapping_keys = [(m.user_id, m.repo_id) for m in mappings]

            # Get all existing mappings in a single query
            existing_mappings = {
                (m.user_id, m.repo_id): m
                for m in session.query(UserRepositoryMap).filter(
                    sqlalchemy.tuple_(
                        UserRepositoryMap.user_id, UserRepositoryMap.repo_id
                    ).in_(mapping_keys)
                )
            }

            # Process all mappings
            for mapping in mappings:
                key = (mapping.user_id, mapping.repo_id)
                if key in existing_mappings:
                    # Update only the admin field for existing mappings
                    existing_mapping = existing_mappings[key]
                    existing_mapping.admin = mapping.admin
                else:
                    # Add new mapping to the session
                    session.add(mapping)

            # Commit all changes
            session.commit()

    @classmethod
    def get_instance(cls, config: OpenHandsConfig) -> UserRepositoryMapStore:
        """Get an instance of the UserRepositoryMapStore."""
        return UserRepositoryMapStore(session_maker, config)
