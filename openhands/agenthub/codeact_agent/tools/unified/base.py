"""Base Tool class and related exceptions for OpenHands tools."""

import json
from abc import ABC, abstractmethod
from typing import Any

from litellm import ChatCompletionToolParam

from openhands.core.exceptions import FunctionCallValidationError
# Backwards-compat alias for legacy imports
ToolValidationError = FunctionCallValidationError


class Tool(ABC):
    """Base class for all OpenHands tools.

    This class encapsulates tool definitions and parameter validation.
    Action creation is handled by the function calling layer.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_schema(
        self, use_short_description: bool = False
    ) -> ChatCompletionToolParam:
        """Get the tool schema for function calling.

        Args:
            use_short_description: Whether to use a shorter description

        Returns:
            Tool schema compatible with LiteLLM function calling
        """
        pass

    @abstractmethod
    def validate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tool parameters.

        Args:
            parameters: Raw parameters from function call

        Returns:
            Validated and normalized parameters

        Raises:
            FunctionCallValidationError: If parameters are invalid
        """
        pass

    def validate_function_call(self, function_call: Any) -> dict[str, Any]:
        """Validate a function call and return normalized parameters.

        Args:
            function_call: Function call object from LLM

        Returns:
            Validated and normalized parameters

        Raises:
            FunctionCallValidationError: If function call is invalid
        """
        try:
            # Parse function call arguments
            if hasattr(function_call, 'arguments'):
                arguments_str = function_call.arguments
            else:
                arguments_str = str(function_call)

            try:
                parameters = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                raise FunctionCallValidationError(
                    f'Failed to parse function call arguments: {arguments_str}. Error: {e}'
                ) from e

            # Validate parameters
            return self.validate_parameters(parameters)

        except FunctionCallValidationError:
            raise
        except Exception as e:
            raise FunctionCallValidationError(
                f'Unexpected error validating function call: {e}'
            ) from e

    def __str__(self) -> str:
        return f'Tool({self.name})'

    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', description='{self.description[:50]}...')"
