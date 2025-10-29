from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from storage.stored_conversation_metadata_saas import StoredConversationMetadataSaas

from openhands.app_server.app_conversation.app_conversation_models import (
    AppConversationInfo,
    AppConversationInfoPage,
    AppConversationSortOrder,
)
from openhands.app_server.app_conversation.sql_app_conversation_info_service import (
    SQLAppConversationInfoService as _SQLAppConversationInfoService,
)
from openhands.app_server.app_conversation.sql_app_conversation_info_service import (
    StoredConversationMetadata as _StoredConversationMetadata,
)

StoredConversationMetadata = _StoredConversationMetadata


class SQLAppConversationInfoServiceSaas(_SQLAppConversationInfoService):
    """Extended SQLAppConversationInfoService with user-based filtering and SAAS metadata handling."""

    async def _secure_select(self):
        query = (
            select(StoredConversationMetadata)
            .join(
                StoredConversationMetadataSaas,
                StoredConversationMetadata.conversation_id
                == StoredConversationMetadataSaas.conversation_id,
            )
            .where(StoredConversationMetadata.conversation_version == 'V1')
        )

        user_id = await self.user_context.get_user_id()
        if user_id:
            query = query.where(StoredConversationMetadataSaas.user_id == user_id)

        return query

    async def _secure_select_with_saas_metadata(self):
        """Select query that includes SAAS metadata for retrieving user_id."""
        query = (
            select(StoredConversationMetadata, StoredConversationMetadataSaas)
            .join(
                StoredConversationMetadataSaas,
                StoredConversationMetadata.conversation_id
                == StoredConversationMetadataSaas.conversation_id,
            )
            .where(StoredConversationMetadata.conversation_version == 'V1')
        )

        user_id = await self.user_context.get_user_id()
        if user_id:
            query = query.where(StoredConversationMetadataSaas.user_id == user_id)

        return query

    async def search_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
        sort_order: AppConversationSortOrder = AppConversationSortOrder.CREATED_AT_DESC,
        page_id: str | None = None,
        limit: int = 100,
    ) -> AppConversationInfoPage:
        """Search for conversations with user_id from SAAS metadata."""
        query = await self._secure_select_with_saas_metadata()

        query = self._apply_filters_with_saas_metadata(
            query=query,
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

        # Add sort order
        if sort_order == AppConversationSortOrder.CREATED_AT:
            query = query.order_by(StoredConversationMetadata.created_at)
        elif sort_order == AppConversationSortOrder.CREATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.created_at.desc())
        elif sort_order == AppConversationSortOrder.UPDATED_AT:
            query = query.order_by(StoredConversationMetadata.last_updated_at)
        elif sort_order == AppConversationSortOrder.UPDATED_AT_DESC:
            query = query.order_by(StoredConversationMetadata.last_updated_at.desc())
        elif sort_order == AppConversationSortOrder.TITLE:
            query = query.order_by(StoredConversationMetadata.title)
        elif sort_order == AppConversationSortOrder.TITLE_DESC:
            query = query.order_by(StoredConversationMetadata.title.desc())

        # Apply pagination
        if page_id is not None:
            try:
                offset = int(page_id)
                query = query.offset(offset)
            except ValueError:
                # If page_id is not a valid integer, start from beginning
                offset = 0
        else:
            offset = 0

        # Apply limit and get one extra to check if there are more results
        query = query.limit(limit + 1)

        result = await self.db_session.execute(query)
        rows = result.all()

        # Check if there are more results
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [self._to_info_with_user_id(stored_metadata, saas_metadata) 
                for stored_metadata, saas_metadata in rows]

        # Calculate next page ID
        next_page_id = None
        if has_more:
            next_page_id = str(offset + limit)

        return AppConversationInfoPage(items=items, next_page_id=next_page_id)

    async def count_app_conversation_info(
        self,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ) -> int:
        """Count conversations matching the given filters with SAAS metadata."""
        query = select(func.count(StoredConversationMetadata.conversation_id)).select_from(
            StoredConversationMetadata.join(
                StoredConversationMetadataSaas,
                StoredConversationMetadata.conversation_id
                == StoredConversationMetadataSaas.conversation_id,
            )
        ).where(StoredConversationMetadata.conversation_version == 'V1')

        # Apply user filtering
        user_id = await self.user_context.get_user_id()
        if user_id:
            query = query.where(StoredConversationMetadataSaas.user_id == user_id)

        query = self._apply_filters_with_saas_metadata(
            query=query,
            title__contains=title__contains,
            created_at__gte=created_at__gte,
            created_at__lt=created_at__lt,
            updated_at__gte=updated_at__gte,
            updated_at__lt=updated_at__lt,
        )

        result = await self.db_session.execute(query)
        count = result.scalar()
        return count or 0

    def _apply_filters_with_saas_metadata(
        self,
        query,
        title__contains: str | None = None,
        created_at__gte: datetime | None = None,
        created_at__lt: datetime | None = None,
        updated_at__gte: datetime | None = None,
        updated_at__lt: datetime | None = None,
    ):
        """Apply filters to query that includes SAAS metadata."""
        # Apply the same filters as the base class
        conditions = []
        if title__contains is not None:
            conditions.append(
                StoredConversationMetadata.title.like(f'%{title__contains}%')
            )

        if created_at__gte is not None:
            conditions.append(StoredConversationMetadata.created_at >= created_at__gte)

        if created_at__lt is not None:
            conditions.append(StoredConversationMetadata.created_at < created_at__lt)

        if updated_at__gte is not None:
            conditions.append(
                StoredConversationMetadata.last_updated_at >= updated_at__gte
            )

        if updated_at__lt is not None:
            conditions.append(
                StoredConversationMetadata.last_updated_at < updated_at__lt
            )

        if conditions:
            query = query.where(*conditions)
        return query

    async def get_app_conversation_info(
        self, conversation_id: UUID
    ) -> AppConversationInfo | None:
        """Get conversation info with user_id from SAAS metadata."""
        query = await self._secure_select_with_saas_metadata()
        query = query.where(
            StoredConversationMetadata.conversation_id == str(conversation_id)
        )
        result_set = await self.db_session.execute(query)
        result = result_set.first()
        if result:
            stored_metadata, saas_metadata = result
            return self._to_info_with_user_id(stored_metadata, saas_metadata)
        return None

    async def batch_get_app_conversation_info(
        self, conversation_ids: list[UUID]
    ) -> list[AppConversationInfo | None]:
        """Batch get conversation info with user_id from SAAS metadata."""
        conversation_id_strs = [
            str(conversation_id) for conversation_id in conversation_ids
        ]
        query = await self._secure_select_with_saas_metadata()
        query = query.where(
            StoredConversationMetadata.conversation_id.in_(conversation_id_strs)
        )
        result = await self.db_session.execute(query)
        rows = result.all()
        
        # Create a mapping of conversation_id to (metadata, saas_metadata)
        info_by_id = {}
        for stored_metadata, saas_metadata in rows:
            info_by_id[stored_metadata.conversation_id] = (stored_metadata, saas_metadata)
        
        results: list[AppConversationInfo | None] = []
        for conversation_id in conversation_id_strs:
            if conversation_id in info_by_id:
                stored_metadata, saas_metadata = info_by_id[conversation_id]
                results.append(self._to_info_with_user_id(stored_metadata, saas_metadata))
            else:
                results.append(None)

        return results

    async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        """Save conversation info and create/update SAAS metadata with user_id and org_id."""
        # Save the base conversation metadata
        await super().save_app_conversation_info(info)
        
        # Get current user_id for SAAS metadata
        user_id = await self.user_context.get_user_id()
        if user_id:
            # Check if SAAS metadata already exists
            saas_query = select(StoredConversationMetadataSaas).where(
                StoredConversationMetadataSaas.conversation_id == str(info.id)
            )
            result = await self.db_session.execute(saas_query)
            existing_saas_metadata = result.scalar_one_or_none()
            
            if existing_saas_metadata:
                # Update existing SAAS metadata
                existing_saas_metadata.user_id = user_id
                # Keep existing org_id or set to user_id if not specified
                if not existing_saas_metadata.org_id:
                    existing_saas_metadata.org_id = user_id
            else:
                # Create new SAAS metadata
                # Set org_id to user_id as specified in requirements
                saas_metadata = StoredConversationMetadataSaas(
                    conversation_id=str(info.id),
                    user_id=user_id,
                    org_id=user_id,  # Set org_id to user_id as it will not be specified
                )
                self.db_session.add(saas_metadata)
            
            await self.db_session.commit()
        
        return info

    def _to_info_with_user_id(
        self, 
        stored: StoredConversationMetadata, 
        saas_metadata: StoredConversationMetadataSaas
    ) -> AppConversationInfo:
        """Convert stored metadata to AppConversationInfo with user_id from SAAS metadata."""
        # Use the base _to_info method to get the basic info
        info = self._to_info(stored)
        
        # Override the created_by_user_id with the user_id from SAAS metadata
        info.created_by_user_id = str(saas_metadata.user_id) if saas_metadata.user_id else None
        
        return info


# Re-export for backward compatibility
SQLAppConversationInfoService = SQLAppConversationInfoServiceSaas


__all__ = ['StoredConversationMetadata', 'SQLAppConversationInfoService']
