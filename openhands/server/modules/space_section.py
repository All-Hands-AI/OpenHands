from sqlalchemy import and_, delete

from openhands.core.logger import openhands_logger as logger
from openhands.server.db import database
from openhands.server.models import SpaceSectionAction, SpaceSectionConfig


class SpaceSectionModule:
    async def _get_space_section_config(self, space_id: int, space_section_id: int):
        """
        Get space section config by space_id and space_section_id
        """
        try:
            query = SpaceSectionConfig.select().where(
                and_(
                    SpaceSectionConfig.c.space_id == space_id,
                    SpaceSectionConfig.c.space_section_id == space_section_id,
                )
            )
            existing_record = await database.fetch_one(query)
            return existing_record
        except Exception as e:
            logger.error(f'Error getting space section config: {str(e)}')
            return None

    async def _update_space_section_config_hash(
        self, space_id: int, space_section_id: int, hash_config: str
    ):
        """
        Update hash_config for space section config
        """
        try:
            await database.execute(
                SpaceSectionConfig.update()
                .where(
                    and_(
                        SpaceSectionConfig.c.space_id == space_id,
                        SpaceSectionConfig.c.space_section_id == space_section_id,
                    )
                )
                .values(hash_config=hash_config)
            )
            return True
        except Exception as e:
            logger.error(f'Error updating space section config hash: {str(e)}')
            return False

    async def _delete_space_section_actions(self, space_id: int, space_section_id: int):
        """
        Delete all space section actions for a specific space_id and space_section_id
        """
        try:
            query = delete(SpaceSectionAction).where(
                and_(
                    SpaceSectionAction.c.space_id == space_id,
                    SpaceSectionAction.c.space_section_id == space_section_id,
                )
            )
            result = await database.execute(query)
            return result
        except Exception as e:
            logger.error(f'Error deleting space section actions: {str(e)}')
            return None

    async def _upsert_space_section_config(
        self, space_id: int, space_section_id: int, hash_config: str
    ):
        try:
            # Use named parameters for SQLAlchemy
            sql = """
            INSERT INTO space_section_configs (space_id, space_section_id, hash_config)
            VALUES (:space_id, :space_section_id, :hash_config)
            ON CONFLICT (space_id, space_section_id)
            DO UPDATE SET
                hash_config = EXCLUDED.hash_config,
                updated_at = CURRENT_TIMESTAMP
        """

            await database.execute(
                sql,
                {
                    'space_id': space_id,
                    'space_section_id': space_section_id,
                    'hash_config': hash_config,
                },
            )
            return True
        except Exception as e:
            logger.error(f'Error upserting space section config with raw SQL: {str(e)}')
            return False


space_section_module = SpaceSectionModule()
