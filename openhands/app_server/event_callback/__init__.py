"""Event callback system for OpenHands.

This module provides the event callback system that allows processors to be
registered and executed when specific events occur during conversations.

All callback processors must be imported here to ensure they are registered
with the discriminated union system used by Pydantic for validation.
"""

# Import all callback processors to register them with the discriminated union
from .event_callback_models import EventCallbackProcessor, LoggingCallbackProcessor
from .github_v1_callback_processor import GithubV1CallbackProcessor
from .set_title_callback_processor import SetTitleCallbackProcessor

__all__ = [
    'EventCallbackProcessor',
    'LoggingCallbackProcessor',
    'GithubV1CallbackProcessor',
    'SetTitleCallbackProcessor',
]
