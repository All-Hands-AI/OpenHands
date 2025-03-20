"""Utility for generating conversation titles."""

from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.core.config import AppConfig


async def generate_conversation_title(message_content: str, llm: LLM) -> str:
    """Generate a concise title for a conversation based on the first user message.
    
    Args:
        message_content: The content of the first user message
        llm: The LLM instance to use for generating the title
        
    Returns:
        A concise title for the conversation
    """
    try:
        # Create a prompt for the LLM to generate a title
        prompt = f"""Generate a concise title (5 words or less) for a conversation that starts with this message:
        
"{message_content}"

The title should be descriptive but brief. Return ONLY the title text with no additional explanation or formatting.
"""
        
        # Call the LLM to generate a title
        response = await llm.acompletion(prompt, max_tokens=50)
        title = response.strip()
        
        # Limit title length if it's too long
        if len(title) > 50:
            title = title[:47] + "..."
            
        logger.info(f"Generated conversation title: {title}")
        return title
    except Exception as e:
        logger.error(f"Error generating conversation title: {e}")
        return "New Conversation"  # Fallback title