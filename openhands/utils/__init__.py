"""
OpenHands utilities package
"""

from .encoding import (
    DEFAULT_ENCODING,
    FALLBACK_ENCODINGS,
    ERROR_HANDLING,
    get_system_encoding,
    get_preferred_encoding,
    get_fallback_encodings,
    open_text_file,
    read_text_file,
    write_text_file,
    open_binary_file,
    safe_read,
    safe_write,
    safe_open,
)

__all__ = [
    'DEFAULT_ENCODING',
    'FALLBACK_ENCODINGS', 
    'ERROR_HANDLING',
    'get_system_encoding',
    'get_preferred_encoding',
    'get_fallback_encodings',
    'open_text_file',
    'read_text_file',
    'write_text_file',
    'open_binary_file',
    'safe_read',
    'safe_write',
    'safe_open',
]
