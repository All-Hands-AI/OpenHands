"""Utility functions for generating conversation summaries."""

from typing import Optional

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.events.event_store import EventStore
from openhands.llm.llm import LLM
from openhands.storage.data_models.settings import Settings
from openhands.storage.files import FileStore


async def generate_conversation_title(
    message: str, llm_config: LLMConfig, max_length: int = 50
) -> Optional[str]:
    """Generate a concise title for a conversation based on the first user message.

    Args:
        message: The first user message in the conversation.
        llm_config: The LLM configuration to use for generating the title.
        max_length: The maximum length of the generated title.

    Returns:
        A concise title for the conversation, or None if generation fails.
    """
    if not message or message.strip() == '':
        return None

    # Truncate very long messages to avoid excessive token usage
    if len(message) > 1000:
        truncated_message = message[:1000] + '...(truncated)'
    else:
        truncated_message = message

    try:
        llm = LLM(llm_config)

        # Create a simple prompt for the LLM to generate a title
        messages = [
            {
                'role': 'system',
                'content': 'You are a helpful assistant that generates concise, descriptive titles for conversations with OpenHands. OpenHands is a helpful AI agent that can interact with a computer to solve tasks using bash terminal, file editor, and browser. Given a user message (which may be truncated), generate a concise, descriptive title for the conversation. Return only the title, with no additional text, quotes, or explanations.',
            },
            {
                'role': 'user',
                'content': f'Generate a title (maximum {max_length} characters) for a conversation that starts with this message:\n\n{truncated_message}',
            },
        ]

        response = llm.completion(messages=messages)
        title = response.choices[0].message.content.strip()

        # Ensure the title isn't too long
        if len(title) > max_length:
            title = title[: max_length - 3] + '...'

        return title
    except Exception as e:
        logger.error(f'Error generating conversation title: {e}')
        return None


def get_default_conversation_title(conversation_id: str) -> str:
    """
    Generate a default title for a conversation based on its ID.

    Args:
        conversation_id: The ID of the conversation

    Returns:
        A default title string
    """
    return f'Conversation {conversation_id[:5]}'


async def auto_generate_title(
    conversation_id: str, user_id: str | None, file_store: FileStore, settings: Settings
) -> str:
    """
    Auto-generate a title for a conversation based on the first user message.
    Uses LLM-based title generation if available, otherwise falls back to a simple truncation.

    Args:
        conversation_id: The ID of the conversation
        user_id: The ID of the user

    Returns:
        A generated title string
    """
    logger.info(f'auto_generate_title called for conversation {conversation_id}, user_id: {user_id}')
    try:
        # Create an event store for the conversation
        event_store = EventStore(conversation_id, file_store, user_id)
        logger.info(f'Created event store for conversation {conversation_id}')

        # Find the first user message
        first_user_message = None
        event_count = 0
        for event in event_store.search_events():
            event_count += 1
            logger.debug(f'Checking event {event_count}: {event.__class__.__name__}, source: {event.source}')
            if (
                event.source == EventSource.USER
                and isinstance(event, MessageAction)
                and event.content
                and event.content.strip()
            ):
                first_user_message = event.content
                logger.info(f'Found first user message in conversation {conversation_id}: "{first_user_message[:100]}..."')
                break

        logger.info(f'Searched {event_count} events in conversation {conversation_id}')
        
        if first_user_message:
            logger.info(f'Processing first user message for title generation in conversation {conversation_id}')
            # Get LLM config from user settings
            try:
                if settings and settings.llm_model:
                    logger.info(f'Using LLM model {settings.llm_model} for title generation in conversation {conversation_id}')
                    # Create LLM config from settings
                    llm_config = LLMConfig(
                        model=settings.llm_model,
                        api_key=settings.llm_api_key,
                        base_url=settings.llm_base_url,
                    )

                    # Try to generate title using LLM
                    logger.info(f'Calling LLM for title generation in conversation {conversation_id}')
                    llm_title = await generate_conversation_title(
                        first_user_message, llm_config
                    )
                    if llm_title:
                        logger.info(f'Generated title using LLM for conversation {conversation_id}: "{llm_title}"')
                        return llm_title
                    else:
                        logger.warning(f'LLM returned empty title for conversation {conversation_id}')
                else:
                    logger.info(f'No LLM model configured for conversation {conversation_id}, skipping LLM title generation')
            except Exception as e:
                logger.error(f'Error using LLM for title generation in conversation {conversation_id}: {e}')

            # Fall back to simple truncation if LLM generation fails or is unavailable
            logger.info(f'Falling back to truncation-based title for conversation {conversation_id}')
            first_user_message = first_user_message.strip()
            title = first_user_message[:30]
            if len(first_user_message) > 30:
                title += '...'
            logger.info(f'Generated title using truncation for conversation {conversation_id}: "{title}"')
            return title
        else:
            logger.warning(f'No first user message found for conversation {conversation_id}, cannot generate title')
    except Exception as e:
        logger.error(f'Error generating title for conversation {conversation_id}: {str(e)}')
    logger.info(f'Returning empty title for conversation {conversation_id}')
    return ''
