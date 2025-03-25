"""Utility functions for generating conversation summaries."""

from typing import Optional

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action.message import MessageAction
from openhands.events.event import EventSource
from openhands.llm.llm import LLM
from openhands.storage.conversation.conversation_store import ConversationStore


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
    truncated_message = message[:1000] if len(message) > 1000 else message

    try:
        llm = LLM(llm_config)

        # Create a simple prompt for the LLM to generate a title
        messages = [
            {
                'role': 'system',
                'content': f'Generate a concise, descriptive title (maximum {max_length} characters) for a conversation that starts with the following message. The title should summarize the main topic or request. Return only the title, with no additional text, quotes, or explanations.',
            },
            {'role': 'user', 'content': truncated_message},
        ]

        response = await llm.completion(messages=messages)
        title = response.choices[0].message.content.strip()

        # Ensure the title isn't too long
        if len(title) > max_length:
            title = title[: max_length - 3] + '...'

        return title
    except Exception as e:
        logger.error(f'Error generating conversation title: {e}')
        return None


async def update_conversation_title_if_needed(
    conversation_id: str,
    conversation_store: ConversationStore,
    event_stream=None,
    llm_config: Optional[LLMConfig] = None,
) -> bool:
    """Update the conversation title if it's a default title and there's a user message.

    Args:
        conversation_id: The ID of the conversation to update.
        conversation_store: The conversation store to use for retrieving and updating metadata.
        event_stream: Optional event stream to use. If not provided, it will be created.
        llm_config: The LLM configuration to use for generating the title.

    Returns:
        True if the title was updated, False otherwise.
    """
    try:
        # Get the conversation metadata
        metadata = await conversation_store.get_metadata(conversation_id)
        if not metadata:
            logger.warning(f'No metadata found for conversation {conversation_id}')
            return False

        # Check if the title is a default title (contains the conversation ID)
        if metadata.title and conversation_id[:5] not in metadata.title:
            # Not a default title, no need to update
            return False

        # If we don't have an event stream, we can't proceed
        if not event_stream:
            logger.warning(
                f'No event stream provided for conversation {conversation_id}'
            )
            return False

        # Find the first MessageAction from the user
        first_user_message = None
        for event in event_stream.get_events():
            if (
                isinstance(event, MessageAction)
                and event.source == EventSource.USER
                and event.content
                and event.content.strip()
            ):
                first_user_message = event.content
                break

        if not first_user_message:
            # No user message found
            return False

        # If we don't have an LLM config, we can't generate a title
        if not llm_config:
            logger.warning(f'No LLM config provided for conversation {conversation_id}')
            return False

        # Generate a new title
        new_title = await generate_conversation_title(first_user_message, llm_config)
        if not new_title:
            return False

        # Update the conversation metadata
        metadata.title = new_title
        await conversation_store.save_metadata(metadata)
        logger.info(f'Updated title for conversation {conversation_id}: {new_title}')
        return True

    except Exception as e:
        logger.error(f'Error updating conversation title: {e}')
        return False
