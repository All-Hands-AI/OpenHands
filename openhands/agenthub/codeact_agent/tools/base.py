from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from litellm import ChatCompletionToolParam

from openhands.core.exceptions import FunctionCallValidationError


class Tool(ABC):
    """Base class for CodeAct tools.

    Subclasses should encapsulate schema, descriptions and validation.
    They must implement to_param() and to_action().
    """

    @abstractmethod
    def to_param(self) -> ChatCompletionToolParam:
        """Return the ChatCompletionToolParam schema for this tool."""
        raise NotImplementedError

    def parse_arguments(self, raw_arguments: str) -> dict[str, Any]:
        """Parse the raw JSON string from the model into a dict.

        Raises FunctionCallValidationError on failure.
        """
        try:
            return json.loads(raw_arguments) if raw_arguments else {}
        except json.decoder.JSONDecodeError as e:
            raise FunctionCallValidationError(
                f'Failed to parse tool call arguments: {raw_arguments}'
            ) from e

    @abstractmethod
    def to_action(self, arguments: dict[str, Any]):  # -> Action
        """Convert validated arguments to an Action.

        Implementations should raise FunctionCallValidationError for
        missing/invalid parameters.
        """
        raise NotImplementedError
