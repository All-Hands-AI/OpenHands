import copy
import os
import re
import tempfile
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, TypeVar, Union

from openhands.core.config import AppConfig
from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    FileEditAction,
    FileReadAction,
    FileWriteAction,
)
from openhands.events.observation import (
    ErrorObservation,
    FatalErrorObservation,
    FileEditObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.linter import DefaultLinter
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics
from openhands.utils.chunk_localizer import Chunk, get_top_k_chunk_matches
from openhands.utils.diff import get_diff


T = TypeVar('T')

def edit_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for edit operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> T:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f'Error during {operation_name}: {e}')
                if operation_name == "validate_range":
                    return ErrorObservation(f'Invalid range for editing: {str(e)}')
                elif operation_name == "lint":
                    return ErrorObservation(f'Linting error: {str(e)}')
                return FatalErrorObservation(f'Fatal error during {operation_name}: {str(e)}')
        return wrapper
    return decorator


SYS_MSG = """Your job is to produce a new version of the file based on the old version and the
provided draft of the new version. The provided draft may be incomplete (it may skip lines) and/or incorrectly indented. You should try to apply the changes present in the draft to the old version, and output a new version of the file.
NOTE:
- The output file should be COMPLETE and CORRECTLY INDENTED. Do not omit any lines, and do not change any lines that are not part of the changes.
- You should output the new version of the file by wrapping the new version of the file content in a 
