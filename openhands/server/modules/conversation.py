import select
from openhands.server.models import Conversation, User
from openhands.server.db import database
from openhands.core.logger import openhands_logger as logger
from sqlalchemy import select


class ConversationModule:
    async def _get_conversation_visibility(self, conversation_id: str, user_id: str):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id) &
                (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)
            return existing_record.published if existing_record else False
        except Exception as e:
            logger.error(f'Error getting conversation visibility: {str(e)}')
            return False

    async def _update_conversation_visibility(self, conversation_id: str, is_published: bool, user_id: str):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id) &
                (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)

            if existing_record:
                await database.execute(
                    Conversation.update()
                    .where(
                        (Conversation.c.conversation_id == conversation_id) &
                        (Conversation.c.user_id == user_id)
                    )
                    .values(published=is_published)
                )
            else:
                await database.execute(
                    Conversation.insert().values(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        published=is_published
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
            query = Conversation.select().where(Conversation.c.conversation_id == conversation_id)
            existing_record = await database.fetch_one(query)
            if not existing_record:
                return 'Conversation not found', None
            if not existing_record.published:
                return 'Conversation not published', None
            user_id = existing_record.user_id
            user_query = select(User).where(User.c.public_key == user_id.lower())
            user = await database.fetch_one(user_query)
            if not user:
                return 'User not found', None
            return None, {'mnemonic': user['mnemonic'], 'user_id': user_id}
        except Exception as e:
            logger.error(f'Error getting conversation visibility by id: {str(e)}')
            return 'Error getting conversation visibility by id', None

    async def _delete_conversation(self, conversation_id: str, user_id: str):
        try:
            query = Conversation.select().where(
                (Conversation.c.conversation_id == conversation_id) &
                (Conversation.c.user_id == user_id)
            )
            existing_record = await database.fetch_one(query)
            if not existing_record:
                return 'Conversation not found', None
            await database.execute(
                Conversation.delete().where(
                    (Conversation.c.conversation_id == conversation_id) &
                    (Conversation.c.user_id == user_id)
                )
            )
            return True
        except Exception as e:
            logger.error(f'Error deleting conversation: {str(e)}')
            return False


conversation_module = ConversationModule()
