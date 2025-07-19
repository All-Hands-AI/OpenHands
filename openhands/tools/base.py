"""Base Tool class and related exceptions for OpenHands tools."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from litellm import ChatCompletionToolParam
from pydantic import BaseModel, ValidationError

from openhands.events.action import Action
from openhands.events.observation import Observation


class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolValidationError(ToolError):
    """Exception raised when tool parameters fail validation."""
    pass


class ToolResult(BaseModel):
    """Result of a tool operation."""
    success: bool
    action: Optional[Action] = None
    error: Optional[str] = None
    observation: Optional[Observation] = None


class Tool(ABC):
    """Base class for all OpenHands tools.
    
    This class encapsulates tool definitions, parameter validation,
    action creation, and error handling.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_schema(self, use_short_description: bool = False) -> ChatCompletionToolParam:
        """Get the tool schema for function calling.
        
        Args:
            use_short_description: Whether to use a shorter description
            
        Returns:
            Tool schema compatible with LiteLLM function calling
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize tool parameters.
        
        Args:
            parameters: Raw parameters from function call
            
        Returns:
            Validated and normalized parameters
            
        Raises:
            ToolValidationError: If parameters are invalid
        """
        pass
    
    @abstractmethod
    def create_action(self, parameters: Dict[str, Any], thought: str = "") -> Action:
        """Create an OpenHands action from validated parameters.
        
        Args:
            parameters: Validated parameters
            thought: Optional thought/reasoning for the action
            
        Returns:
            OpenHands action ready for execution
        """
        pass
    
    def process_function_call(self, function_call: Any, thought: str = "") -> ToolResult:
        """Process a function call and create an action.
        
        Args:
            function_call: Function call object from LLM
            thought: Optional thought/reasoning
            
        Returns:
            ToolResult containing the action or error
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
                return ToolResult(
                    success=False,
                    error=f"Failed to parse function call arguments: {arguments_str}. Error: {e}"
                )
            
            # Validate parameters
            validated_params = self.validate_parameters(parameters)
            
            # Create action
            action = self.create_action(validated_params, thought)
            
            return ToolResult(success=True, action=action)
            
        except ToolValidationError as e:
            return ToolResult(success=False, error=str(e))
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Unexpected error processing function call: {e}"
            )
    
    def interpret_observation(self, observation: Observation) -> str:
        """Interpret an observation and provide human-readable feedback.
        
        Args:
            observation: Observation from action execution
            
        Returns:
            Human-readable interpretation of the observation
        """
        # Default implementation - subclasses can override for custom interpretation
        if hasattr(observation, 'content'):
            return observation.content
        return str(observation)
    
    def __str__(self) -> str:
        return f"Tool({self.name})"
    
    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', description='{self.description[:50]}...')"