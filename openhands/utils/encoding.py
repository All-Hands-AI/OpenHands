"""
Unified encoding configuration and utilities.

This module provides a single place to manage text/binary file I/O encodings
for the OpenHands project to ensure cross‑platform compatibility, especially
on Windows.
"""

import os
import sys
from typing import TextIO, BinaryIO, Union, Optional

from openhands.core.encoding_config import encoding_config


# 统一编码配置（从配置类导入）
DEFAULT_ENCODING = encoding_config.DEFAULT_ENCODING
FALLBACK_ENCODINGS = encoding_config.FALLBACK_ENCODINGS
ERROR_HANDLING = encoding_config.ERROR_HANDLING


def get_system_encoding() -> str:
    """Return the system default encoding."""
    return sys.getdefaultencoding()


def get_preferred_encoding() -> str:
    """Return the preferred text encoding."""
    return DEFAULT_ENCODING


def get_fallback_encodings() -> list[str]:
    """Return the list of fallback encodings to try."""
    return FALLBACK_ENCODINGS.copy()


def open_text_file(
    file_path: Union[str, os.PathLike],
    mode: str = 'r',
    encoding: Optional[str] = None,
    errors: str = ERROR_HANDLING,
    **kwargs
) -> TextIO:
    """
    Open a text file using the unified encoding configuration.

    Args:
        file_path: Path to the file.
        mode: File open mode ('r', 'w', 'a', 'r+', 'w+', 'a+').
        encoding: Explicit encoding. If None, the preferred encoding is used.
        errors: Error handling strategy.
        **kwargs: Additional arguments passed to built‑in open().

    Returns:
        A text file object.
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    # Ensure the parent directory exists for write/append/create modes
    if 'w' in mode or 'a' in mode or 'x' in mode:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    return open(file_path, mode, encoding=encoding, errors=errors, **kwargs)


def read_text_file(
    file_path: Union[str, os.PathLike],
    encoding: Optional[str] = None,
    fallback_encodings: Optional[list[str]] = None
) -> str:
    """
    Read a text file, automatically trying multiple encodings.

    Args:
        file_path: Path to the file.
        encoding: Preferred encoding.
        fallback_encodings: Fallback encodings to try.

    Returns:
        The file contents as a string.

    Raises:
        UnicodeDecodeError: Raised if all encodings fail.
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    if fallback_encodings is None:
        fallback_encodings = encoding_config.get_fallback_encodings()
    
    # Try the preferred encoding first
    try:
        with open_text_file(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    
    # Try fallback encodings
    for fallback_encoding in fallback_encodings:
        try:
            with open_text_file(file_path, 'r', encoding=fallback_encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # As a last resort, use replacement for undecodable bytes
    try:
        with open_text_file(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        raise UnicodeDecodeError(
            encoding, b'', 0, 1, f"Unable to decode file with any encoding: {e}"
        )


def write_text_file(
    file_path: Union[str, os.PathLike],
    content: str,
    encoding: Optional[str] = None,
    **kwargs
) -> None:
    """
    Write a text file using the unified encoding configuration.

    Args:
        file_path: Path to the file.
        content: Text content to write.
        encoding: Encoding to use; if None, the preferred encoding is used.
        **kwargs: Additional arguments passed to built‑in open().
    """
    if encoding is None:
        encoding = get_preferred_encoding()
    
    # Ensure the parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open_text_file(file_path, 'w', encoding=encoding, **kwargs) as f:
        f.write(content)


def open_binary_file(
    file_path: Union[str, os.PathLike],
    mode: str = 'rb',
    **kwargs
) -> BinaryIO:
    """
    Open a binary file.

    Args:
        file_path: Path to the file.
        mode: Open mode.
        **kwargs: Additional arguments passed to built‑in open().

    Returns:
        A binary file object.
    """
    # Ensure the parent directory exists for write/append/create modes
    if 'w' in mode or 'a' in mode or 'x' in mode:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return open(file_path, mode, **kwargs)


# Convenience helpers
def safe_read(file_path: Union[str, os.PathLike]) -> str:
    """Safely read a text file, handling encoding automatically."""
    return read_text_file(file_path)


def safe_write(file_path: Union[str, os.PathLike], content: str) -> None:
    """Safely write a text file using the unified encoding configuration."""
    write_text_file(file_path, content)


def safe_open(file_path: Union[str, os.PathLike], mode: str = 'r', **kwargs) -> Union[TextIO, BinaryIO]:
    """Safely open a file, choosing text or binary mode automatically."""
    if 'b' in mode:
        return open_binary_file(file_path, mode, **kwargs)
    else:
        return open_text_file(file_path, mode, **kwargs)
