"""Compatibility shim for legacy imports of Tool and ToolValidationError.

This module re-exports the canonical Tool and FunctionCallValidationError as
ToolValidationError from the new location openhands.agenthub.codeact_agent.tools.base.
"""

from openhands.agenthub.codeact_agent.tools.base import Tool  # noqa: F401
from openhands.core.exceptions import (
    FunctionCallValidationError as ToolValidationError,  # noqa: F401
)
