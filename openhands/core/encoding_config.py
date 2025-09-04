"""
OpenHands encoding configuration.

This module centralizes all encoding‑related configuration used in OpenHands
to ensure cross‑platform compatibility.
"""

import os
import sys
from typing import List


class EncodingConfig:
    """Encoding configuration container."""
    
    # Default encoding
    DEFAULT_ENCODING = 'utf-8'
    
    # Fallback encodings in priority order
    FALLBACK_ENCODINGS = [
        'utf-8-sig',  # UTF-8 with BOM
        'latin-1',    # ISO-8859-1; can decode any byte sequence
        'cp1252',     # Windows-1252
        'gbk',        # Simplified Chinese
        'big5',       # Traditional Chinese
    ]
    
    # Error handling strategy
    ERROR_HANDLING = 'replace'  # use replacement characters
    
    # Platform-specific preferences
    WINDOWS_ENCODINGS = ['cp1252', 'gbk', 'big5']
    UNIX_ENCODINGS = ['utf-8', 'latin-1']
    
    @classmethod
    def get_system_encoding(cls) -> str:
        """Return the system default encoding."""
        return sys.getdefaultencoding()
    
    @classmethod
    def get_preferred_encoding(cls) -> str:
        """Return the preferred encoding."""
        return cls.DEFAULT_ENCODING
    
    @classmethod
    def get_fallback_encodings(cls) -> List[str]:
        """Return a copy of fallback encodings."""
        return cls.FALLBACK_ENCODINGS.copy()
    
    @classmethod
    def get_platform_encodings(cls) -> List[str]:
        """Return platform‑specific preferred encodings."""
        if sys.platform == 'win32':
            return cls.WINDOWS_ENCODINGS.copy()
        else:
            return cls.UNIX_ENCODINGS.copy()
    
    @classmethod
    def get_all_encodings(cls) -> List[str]:
        """Return all encodings considered by the system."""
        encodings = [cls.DEFAULT_ENCODING]
        encodings.extend(cls.get_fallback_encodings())
        return encodings
    
    @classmethod
    def is_encoding_supported(cls, encoding: str) -> bool:
        """Check whether a given encoding is supported."""
        try:
            'test'.encode(encoding)
            return True
        except (LookupError, UnicodeError):
            return False


# Global configuration instance
encoding_config = EncodingConfig()


# Convenience helpers
def get_default_encoding() -> str:
    """Return the default encoding."""
    return encoding_config.get_preferred_encoding()


def get_fallback_encodings() -> List[str]:
    """Return fallback encodings."""
    return encoding_config.get_fallback_encodings()


def get_all_encodings() -> List[str]:
    """Return the list of all encodings."""
    return encoding_config.get_all_encodings()


def is_encoding_supported(encoding: str) -> bool:
    """Check whether an encoding is supported."""
    return encoding_config.is_encoding_supported(encoding)
