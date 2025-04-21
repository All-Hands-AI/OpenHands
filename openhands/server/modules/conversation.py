import asyncio

from openhands.core.logger import openhands_logger as logger
from openhands.server.db import database
from openhands.server.models import Conversation
from openhands.server.shared import (
    ConversationStoreImpl,
    config,
)


class ConversationModule:
    async def _get_conversation_visibility(self, conversation_id: str, user_id: str):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id)
                & (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)

            return {
                'is_published': existing_record.published if existing_record else False,
                'hidden_prompt': existing_record.configs.get('hidden_prompt', True)
                if existing_record
                else True,
            }
        except Exception as e:
            logger.error(f'Error getting conversation visibility: {str(e)}')
            return {'is_published': False, 'hidden_prompt': False}

    async def _update_conversation_visibility(
        self,
        conversation_id: str,
        is_published: bool,
        user_id: str,
        configs: dict,
        title: str,
    ):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id)
                & (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)

            if existing_record:
                await database.execute(
                    Conversation.update()
                    .where(
                        (Conversation.c.conversation_id == conversation_id)
                        & (Conversation.c.user_id == user_id)
                    )
                    .values(published=is_published, configs=configs, title=title)
                )
            else:
                await database.execute(
                    Conversation.insert().values(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        published=is_published,
                        title=title,
                        configs=configs,
                    )
                )
            return True
        except Exception as e:
            logger.error(f'Error updating conversation visibility: {str(e)}')
            return False

    async def _get_conversation_visibility_info(self, conversation_id: str):
        """
        Check if the conversation is published and return the mnemonic of the user who owns the conversation
        """
        try:
            query = Conversation.select().where(
                Conversation.c.conversation_id == conversation_id
            )
            existing_record = await database.fetch_one(query)
            if not existing_record:
                return 'Conversation not found', None
            if not existing_record.published:
                return 'Conversation not published', None
            user_id = existing_record.user_id
            return None, {
                'user_id': user_id,
                'hidden_prompt': existing_record.configs.get('hidden_prompt', True),
            }
        except Exception as e:
            logger.error(f'Error getting conversation visibility by id: {str(e)}')
            return 'Error getting conversation visibility by id', None

    async def _delete_conversation(self, conversation_id: str, user_id: str):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id)
                & (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)
            if not existing_record:
                return 'Conversation not found', None
            await database.execute(
                Conversation.delete().where(
                    (Conversation.c.conversation_id == conversation_id)
                    & (Conversation.c.user_id == user_id)
                )
            )
            return True
        except Exception as e:
            logger.error(f'Error deleting conversation: {str(e)}')
            return False

    async def _get_raw_conversation_info(self, conversation_id: str, user_id: str):
        try:
            conversation_store = await ConversationStoreImpl.get_instance(
                config, user_id, None
            )
            metadata = await conversation_store.get_metadata(conversation_id)
            return {
                'conversation_id': metadata.conversation_id,
                'title': metadata.title,
            }
        except Exception as e:
            logger.error(f'Error getting conversation info: {str(e)}')
            return None

    async def _response_conversation(self, conversations: list[dict]):
        try:
            # Filter conversations without titles
            conversation_updated = [
                conversation
                for conversation in conversations
                if not conversation.get('title')
            ]

            if conversation_updated:
                # Get raw conversation info for those without titles
                tasks = [
                    self._get_raw_conversation_info(
                        conversation.get('conversation_id', ''),
                        conversation.get('user_id', ''),
                    )
                    for conversation in conversation_updated
                ]
                raw_conversations = await asyncio.gather(*tasks)

                raw_conversations_dict = {
                    conversation['conversation_id']: conversation['title']
                    for conversation in raw_conversations
                }

                # Create update tasks for conversations without titles
                update_tasks = []
                for conversation in conversation_updated:
                    if conversation.get('conversation_id') in raw_conversations_dict:
                        update_tasks.append(
                            database.execute(
                                Conversation.update()
                                .where(
                                    (
                                        Conversation.c.conversation_id
                                        == conversation.get('conversation_id')
                                    )
                                    & (
                                        Conversation.c.user_id
                                        == conversation.get('user_id')
                                    )
                                )
                                .values(
                                    title=raw_conversations_dict[
                                        conversation.get('conversation_id')
                                    ]
                                )
                            )
                        )

                # Execute all updates concurrently
                if update_tasks:
                    await asyncio.gather(*update_tasks)

                # Update the titles in our local conversation list
                for conversation in conversations:
                    if (
                        not conversation.get('title')
                        and conversation.get('conversation_id')
                        in raw_conversations_dict
                    ):
                        conversation['title'] = raw_conversations_dict[
                            conversation.get('conversation_id')
                        ]

            # Format and return all conversations
            return [
                {
                    'conversation_id': conversation.get('conversation_id'),
                    'title': conversation.get('title')
                    or 'Untitled Conversation',  # Fallback title
                    'short_description': conversation.get('short_description'),
                    'published': conversation.get('published'),
                    'view_count': 0,
                }
                for conversation in conversations
            ]

        except Exception as e:
            logger.error(f'Error processing conversations: {str(e)}')
            # Return basic format even if error occurs
            return [
                {
                    'conversation_id': conversation.get('conversation_id'),
                    'title': conversation.get('title') or 'Untitled Conversation',
                    'short_description': conversation.get('short_description'),
                    'published': conversation.get('published'),
                    'view_count': 0,
                }
                for conversation in conversations
            ]

    async def _get_list_conversations(self, **kwargs):
        try:
            page = kwargs.get('page', 1)
            limit = kwargs.get('limit', 10)
            offset = (page - 1) * limit
            published = kwargs.get('published')
            conversation_ids = kwargs.get('conversation_ids', [])
            prioritized_usecase_ids = kwargs.get('prioritized_usecase_ids', [])

            query = Conversation.select()

            if published is not None:
                query = query.where(Conversation.c.published == published)
            print('conversation_ids', conversation_ids)
            if conversation_ids and len(conversation_ids) > 0:
                query = query.where(
                    Conversation.c.conversation_id.in_(conversation_ids)
                )

            if page == 1 and len(prioritized_usecase_ids) > 0:
                prioritized_query = query.where(
                    Conversation.c.conversation_id.in_(prioritized_usecase_ids)
                )
                prioritized_items = await database.fetch_all(prioritized_query)

                remaining_query = (
                    query.where(
                        ~Conversation.c.conversation_id.in_(prioritized_usecase_ids)
                    )
                    .offset(0)
                    .limit(limit - len(prioritized_items))
                )
                remaining_items = await database.fetch_all(remaining_query)

                items = [*prioritized_items, *remaining_items]
                items = await self._response_conversation(items)
                return {
                    'items': items,
                    'page': page,
                    'limit': limit,
                }

            # Normal pagination for other pages
            query = query.offset(offset).limit(limit)
            items = await database.fetch_all(query)
            items = await self._response_conversation(items)
            return {
                'items': items,
                'page': page,
                'limit': limit,
            }
        except Exception as e:
            logger.error(f'Error getting list conversations: {str(e)}')
            return []


conversation_module = ConversationModule()
