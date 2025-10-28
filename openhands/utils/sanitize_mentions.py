"""Utilities for sanitizing mentions in text to prevent self-mention loops."""

import os
import re
from typing import Iterable, Optional


def sanitize_mentions(
    text: str, blocklist: Optional[Iterable[str]] = None, replacer: Optional[str] = None
) -> str:
    """Sanitize mentions in text by inserting zero-width joiner after @ symbol.

    Preserves fenced code blocks (```...```) unchanged while sanitizing mentions
    in normal text to prevent clickable/platform-activating mentions.

    Args:
        text: The text to sanitize
        blocklist: List of handles to sanitize (defaults to OpenHands variants)
        replacer: Custom replacement string (defaults to zero-width joiner)

    Returns:
        Sanitized text with mentions neutralized outside code blocks
    """
    if not text:
        return text or ''

    # Default blocklist for OpenHands mentions
    default_blocklist = ['@OpenHands', '@openhands', '@open-hands']
    bl = list(blocklist) if blocklist else default_blocklist

    # Build regex of all variants (case-insensitive)
    escaped = []
    for s in bl:
        if s.startswith('@'):
            escaped.append(re.escape(s))
        else:
            # Match both @handle and handle formats
            escaped.append(re.escape(f'@{s}'))
            escaped.append(re.escape(s))

    pattern = re.compile('(' + '|'.join(escaped) + ')', re.IGNORECASE)

    # Split into fenced code blocks and normal text: ```...```
    parts: list[tuple[str, bool]] = []
    fence = re.compile(r'```[^\n]*\n[\s\S]*?\n```', re.MULTILINE)
    last = 0
    for m in fence.finditer(text):
        if m.start() > last:
            parts.append((text[last : m.start()], False))
        parts.append((text[m.start() : m.end()], True))
        last = m.end()
    if last < len(text):
        parts.append((text[last:], False))

    def neutralize(s: str) -> str:
        def replace_match(match):
            matched_text = match.group(0)
            # If the match doesn't start with @, add it before sanitizing
            if not matched_text.startswith('@'):
                replacement = replacer or '@\u200d'  # zero-width joiner
                return f'{replacement}{matched_text}'
            else:
                replacement = replacer or '@\u200d'  # zero-width joiner
                return matched_text.replace('@', replacement)

        return pattern.sub(replace_match, s)

    return ''.join(chunk if is_code else neutralize(chunk) for chunk, is_code in parts)


def get_default_blocklist() -> list[str]:
    """Get the default list of mentions to sanitize."""
    return ['@OpenHands', '@openhands', '@open-hands']


def get_blocklist_from_env() -> list[str]:
    """Get blocklist from environment variable."""
    env_blocklist = os.getenv('MENTION_BLOCKLIST', '@OpenHands,@openhands,@open-hands')
    return [item.strip() for item in env_blocklist.split(',') if item.strip()]


def sanitize_assistant_message_content(content: str) -> str:
    """Sanitize assistant message content to prevent self-mention loops.

    This is the main function to call for sanitizing assistant message content
    before it's sent to users.

    Args:
        content: The message content to sanitize

    Returns:
        Sanitized content with mentions neutralized outside code blocks
    """
    blocklist = get_blocklist_from_env()
    return sanitize_mentions(content, blocklist=blocklist)
