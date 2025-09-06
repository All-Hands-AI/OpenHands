from __future__ import annotations

from dataclasses import dataclass

from integrations.types import GitLabResourceType
from sqlalchemy import and_, asc, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from storage.database import a_session_maker
from storage.gitlab_webhook import GitlabWebhook

from openhands.core.logger import openhands_logger as logger


@dataclass
class GitlabWebhookStore:
    a_session_maker: sessionmaker = a_session_maker

    @staticmethod
    def determine_resource_type(
        webhook: GitlabWebhook,
    ) -> tuple[GitLabResourceType, str]:
        if not (webhook.group_id or webhook.project_id):
            raise ValueError('Either project_id or group_id must be provided')

        if webhook.group_id and webhook.project_id:
            raise ValueError('Only one of project_id or group_id should be provided')

        if webhook.group_id:
            return (GitLabResourceType.GROUP, webhook.group_id)
        return (GitLabResourceType.PROJECT, webhook.project_id)

    async def store_webhooks(self, project_details: list[GitlabWebhook]) -> None:
        """Store list of project details in db using UPSERT pattern

        Args:
            project_details: List of GitlabWebhook objects to store

        Notes:
            1. Uses UPSERT (INSERT ... ON CONFLICT) to efficiently handle duplicates
            2. Leverages database-level constraints for uniqueness
            3. Performs the operation in a single database transaction
        """
        if not project_details:
            return

        async with self.a_session_maker() as session:
            async with session.begin():
                # Convert GitlabWebhook objects to dictionaries for the insert
                # Using __dict__ and filtering out SQLAlchemy internal attributes and 'id'
                values = [
                    {
                        k: v
                        for k, v in webhook.__dict__.items()
                        if not k.startswith('_') and k != 'id'
                    }
                    for webhook in project_details
                ]

                if values:
                    # Separate values into groups and projects
                    group_values = [v for v in values if v.get('group_id')]
                    project_values = [v for v in values if v.get('project_id')]

                    # Batch insert for groups
                    if group_values:
                        stmt = insert(GitlabWebhook).values(group_values)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['group_id'])
                        await session.execute(stmt)

                    # Batch insert for projects
                    if project_values:
                        stmt = insert(GitlabWebhook).values(project_values)
                        stmt = stmt.on_conflict_do_nothing(
                            index_elements=['project_id']
                        )
                        await session.execute(stmt)

    async def update_webhook(self, webhook: GitlabWebhook, update_fields: dict) -> None:
        """Update a webhook entry based on project_id or group_id.

        Args:
            webhook: GitlabWebhook object containing the updated fields and either project_id or group_id
                     as the identifier. Only one of project_id or group_id should be non-null.

        Raises:
            ValueError: If neither project_id nor group_id is provided, or if both are provided.
        """

        resource_type, resource_id = GitlabWebhookStore.determine_resource_type(webhook)
        async with self.a_session_maker() as session:
            async with session.begin():
                stmt = (
                    update(GitlabWebhook).where(GitlabWebhook.project_id == resource_id)
                    if resource_type == GitLabResourceType.PROJECT
                    else update(GitlabWebhook).where(
                        GitlabWebhook.group_id == resource_id
                    )
                ).values(**update_fields)

                await session.execute(stmt)

    async def delete_webhook(self, webhook: GitlabWebhook) -> None:
        """Delete a webhook entry based on project_id or group_id.

        Args:
            webhook: GitlabWebhook object containing either project_id or group_id
                     as the identifier. Only one of project_id or group_id should be non-null.

        Raises:
            ValueError: If neither project_id nor group_id is provided, or if both are provided.
        """

        resource_type, resource_id = GitlabWebhookStore.determine_resource_type(webhook)

        logger.info(
            'Attempting to delete webhook',
            extra={
                'resource_type': resource_type.value,
                'resource_id': resource_id,
                'user_id': getattr(webhook, 'user_id', None),
            },
        )

        async with self.a_session_maker() as session:
            async with session.begin():
                # Create query based on the identifier provided
                if resource_type == GitLabResourceType.PROJECT:
                    query = GitlabWebhook.__table__.delete().where(
                        GitlabWebhook.project_id == resource_id
                    )
                else:  # has_group_id must be True based on validation
                    query = GitlabWebhook.__table__.delete().where(
                        GitlabWebhook.group_id == resource_id
                    )

                result = await session.execute(query)
                rows_deleted = result.rowcount

                if rows_deleted > 0:
                    logger.info(
                        'Successfully deleted webhook',
                        extra={
                            'resource_type': resource_type.value,
                            'resource_id': resource_id,
                            'rows_deleted': rows_deleted,
                            'user_id': getattr(webhook, 'user_id', None),
                        },
                    )
                else:
                    logger.warning(
                        'No webhook found to delete',
                        extra={
                            'resource_type': resource_type.value,
                            'resource_id': resource_id,
                            'user_id': getattr(webhook, 'user_id', None),
                        },
                    )

    async def update_last_synced(self, webhook: GitlabWebhook) -> None:
        """Update the last_synced timestamp for a webhook to current time.

        This should be called after processing a webhook to ensure it's not
        immediately reprocessed in the next batch.

        Args:
            webhook: GitlabWebhook object containing either project_id or group_id
                     as the identifier. Only one of project_id or group_id should be non-null.

        Raises:
            ValueError: If neither project_id nor group_id is provided, or if both are provided.
        """
        await self.update_webhook(webhook, {'last_synced': text('CURRENT_TIMESTAMP')})

    async def filter_rows(
        self,
        limit: int = 100,
    ) -> list[GitlabWebhook]:
        """Retrieve rows that need processing (webhook doesn't exist on resource).

        Args:
            limit: Maximum number of rows to retrieve (default: 100)

        Returns:
            List of GitlabWebhook objects that need processing
        """

        async with self.a_session_maker() as session:
            query = (
                select(GitlabWebhook)
                .where(GitlabWebhook.webhook_exists.is_(False))
                .order_by(asc(GitlabWebhook.last_synced))
                .limit(limit)
            )
            result = await session.execute(query)
            webhooks = result.scalars().all()

            return list(webhooks)

    async def get_webhook_secret(self, webhook_uuid: str, user_id: str) -> str | None:
        """
        Get's webhook secret given the webhook uuid and admin keycloak user id
        """
        async with self.a_session_maker() as session:
            query = (
                select(GitlabWebhook)
                .where(
                    and_(
                        GitlabWebhook.user_id == user_id,
                        GitlabWebhook.webhook_uuid == webhook_uuid,
                    )
                )
                .limit(1)
            )

            result = await session.execute(query)
            webhooks: list[GitlabWebhook] = list(result.scalars().all())

            if len(webhooks):
                return webhooks[0].webhook_secret
            return None

    @classmethod
    async def get_instance(cls) -> GitlabWebhookStore:
        """Get an instance of the GitlabWebhookStore.

        Returns:
            An instance of GitlabWebhookStore
        """
        return GitlabWebhookStore(a_session_maker)
