"""Base Tool class for CodeAct agent tools."""

import json
from abc import ABC, abstractmethod
from typing import Any

from litellm import ChatCompletionToolParam

from openhands.core.exceptions import FunctionCallValidationError


class Tool(ABC):
    """Base class for all CodeAct tools.

    Encapsulates tool schema definition and parameter validation.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_schema(self, use_short_description: bool = False) -> ChatCompletionToolParam:
        """Return LiteLLM-compatible tool schema."""
        raise NotImplementedError

    @abstractmethod
    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tool parameters.

        Raise FunctionCallValidationError on invalid input.
        """
        raise NotImplementedError

    def validate_function_call(self, function_call: Any) -> dict[str, Any]:
        """Parse JSON arguments from a function call and validate them."""
        arguments_str: str
        if hasattr(function_call, "arguments"):
            arguments_str = function_call.arguments  # type: ignore[attr-defined]
        else:
            arguments_str = str(function_call)
        try:
            params = json.loads(arguments_str)
        except json.JSONDecodeError as e:
            raise FunctionCallValidationError(
                f"Failed to parse function call arguments: {arguments_str}. Error: {e}"
            ) from e
        try:
            return self.validate_parameters(params)
        except FunctionCallValidationError:
            raise
        except Exception as e:
            raise FunctionCallValidationError(
                f"Unexpected error validating function call: {e}"
            ) from e

    def __repr__(self) -> str:  # pragma: no cover
        return f"Tool(name='{self.name}', description='{self.description[:50]}...')"