"""Utility functions for generating conversation summaries."""

from typing import Optional

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


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
