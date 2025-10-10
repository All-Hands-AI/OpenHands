from __future__ import annotations

from typing import List

from server.constants import CURRENT_USER_SETTINGS_VERSION
from server.logger import logger
from storage.database import session_maker
from storage.maintenance_task import MaintenanceTask, MaintenanceTaskProcessor
from storage.saas_settings_store import SaasSettingsStore
from storage.user_settings import UserSettings

from openhands.core.config import load_openhands_config


class UserVersionUpgradeProcessor(MaintenanceTaskProcessor):
    """
    Processor for upgrading user settings to the current version.

    This processor takes a list of user IDs and upgrades any users
    whose user_version is less than CURRENT_USER_SETTINGS_VERSION.
    """

    user_ids: List[str]

    async def __call__(self, task: MaintenanceTask) -> dict:
        """
        Process user version upgrades for the specified user IDs.

        Args:
            task: The maintenance task being processed

        Returns:
            dict: Results containing successful and failed user IDs
        """
        logger.info(
            'user_version_upgrade_processor:start',
            extra={
                'task_id': task.id,
                'user_count': len(self.user_ids),
                'current_version': CURRENT_USER_SETTINGS_VERSION,
            },
        )

        if len(self.user_ids) > 100:
            raise ValueError(
                f'Too many user IDs: {len(self.user_ids)}. Maximum is 100.'
            )

        config = load_openhands_config()

        # Track results
        successful_upgrades = []
        failed_upgrades = []
        users_already_current = []

        # Find users that need upgrading
        with session_maker() as session:
            users_to_upgrade = (
                session.query(UserSettings)
                .filter(
                    UserSettings.keycloak_user_id.in_(self.user_ids),
                    UserSettings.user_version < CURRENT_USER_SETTINGS_VERSION,
                )
                .all()
            )

            # Track users that are already current
            users_needing_upgrade_ids = {u.keycloak_user_id for u in users_to_upgrade}
            users_already_current = [
                uid for uid in self.user_ids if uid not in users_needing_upgrade_ids
            ]

            logger.info(
                'user_version_upgrade_processor:found_users',
                extra={
                    'task_id': task.id,
                    'users_to_upgrade': len(users_to_upgrade),
                    'users_already_current': len(users_already_current),
                    'total_requested': len(self.user_ids),
                },
            )

        # Process each user that needs upgrading
        for user_settings in users_to_upgrade:
            user_id = user_settings.keycloak_user_id
            old_version = user_settings.user_version

            try:
                logger.info(
                    'user_version_upgrade_processor:upgrading_user',
                    extra={
                        'task_id': task.id,
                        'user_id': user_id,
                        'old_version': old_version,
                        'new_version': CURRENT_USER_SETTINGS_VERSION,
                    },
                )

                # Create SaasSettingsStore instance and upgrade
                settings_store = await SaasSettingsStore.get_instance(config, user_id)
                await settings_store.create_default_settings(user_settings)

                successful_upgrades.append(
                    {
                        'user_id': user_id,
                        'old_version': old_version,
                        'new_version': CURRENT_USER_SETTINGS_VERSION,
                    }
                )

                logger.info(
                    'user_version_upgrade_processor:user_upgraded',
                    extra={
                        'task_id': task.id,
                        'user_id': user_id,
                        'old_version': old_version,
                        'new_version': CURRENT_USER_SETTINGS_VERSION,
                    },
                )

            except Exception as e:
                failed_upgrades.append(
                    {'user_id': user_id, 'old_version': old_version, 'error': str(e)}
                )

                logger.error(
                    'user_version_upgrade_processor:user_upgrade_failed',
                    extra={
                        'task_id': task.id,
                        'user_id': user_id,
                        'old_version': old_version,
                        'error': str(e),
                    },
                )

        # Create result summary
        result = {
            'total_users': len(self.user_ids),
            'users_already_current': users_already_current,
            'successful_upgrades': successful_upgrades,
            'failed_upgrades': failed_upgrades,
            'summary': (
                f'Processed {len(self.user_ids)} users: '
                f'{len(successful_upgrades)} upgraded, '
                f'{len(users_already_current)} already current, '
                f'{len(failed_upgrades)} errors'
            ),
        }

        logger.info(
            'user_version_upgrade_processor:completed',
            extra={'task_id': task.id, 'result': result},
        )

        return result
