"""Transport-neutral conversation utilities and facade.

This package provides:
- Conversation: a transport-neutral, attachable conversation facade
- API helpers for attaching/inspecting conversations across runtimes
"""

from .conversation import Conversation  # re-export for convenience

__all__ = ['Conversation']
