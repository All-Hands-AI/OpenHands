"""Tests for the base Tool class and related functionality."""

import json
import pytest
from typing import Any, Dict
from unittest.mock import Mock

from openhands.agenthub.codeact_agent.tools.unified.base import (
    Tool, 
    ToolError, 
    ToolValidationError
)


class MockTool(Tool):
    """Mock tool for testing base functionality."""
    
    def __init__(self, name: str = "mock_tool", description: str = "Mock tool for testing"):
        super().__init__(name, description)
    
    def get_schema(self, use_short_description: bool = False):
        return {
            'type': 'function',
            'function': {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'required_param': {
                            'type': 'string',
                            'description': 'A required parameter'
                        },
                        'optional_param': {
                            'type': 'integer',
                            'description': 'An optional parameter'
                        }
                    },
                    'required': ['required_param']
                }
            }
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(parameters, dict):
            raise ToolValidationError("Parameters must be a dictionary")
        
        if 'required_param' not in parameters:
            raise ToolValidationError("Missing required parameter: required_param")
        
        validated = {'required_param': parameters['required_param']}
        
        if 'optional_param' in parameters:
            if not isinstance(parameters['optional_param'], int):
                raise ToolValidationError("optional_param must be an integer")
            validated['optional_param'] = parameters['optional_param']
        
        return validated


class TestToolError:
    """Test ToolError exception."""
    
    def test_tool_error_creation(self):
        error = ToolError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_tool_error_inheritance(self):
        error = ToolError("Test error")
        assert isinstance(error, Exception)


class TestToolValidationError:
    """Test ToolValidationError exception."""
    
    def test_tool_validation_error_creation(self):
        error = ToolValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, ToolError)
        assert isinstance(error, Exception)
    
    def test_tool_validation_error_inheritance(self):
        error = ToolValidationError("Validation error")
        assert isinstance(error, ToolError)
        assert isinstance(error, Exception)


class TestBaseTool:
    """Test the base Tool class."""
    
    def test_tool_initialization(self):
        tool = MockTool("test_tool", "Test description")
        assert tool.name == "test_tool"
        assert tool.description == "Test description"
    
    def test_tool_initialization_defaults(self):
        tool = MockTool()
        assert tool.name == "mock_tool"
        assert tool.description == "Mock tool for testing"
    
    def test_get_schema(self):
        tool = MockTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'mock_tool'
        assert schema['function']['description'] == 'Mock tool for testing'
        assert 'parameters' in schema['function']
        assert 'required_param' in schema['function']['parameters']['properties']
    
    def test_validate_parameters_success(self):
        tool = MockTool()
        params = {'required_param': 'test_value'}
        validated = tool.validate_parameters(params)
        
        assert validated == {'required_param': 'test_value'}
    
    def test_validate_parameters_with_optional(self):
        tool = MockTool()
        params = {'required_param': 'test_value', 'optional_param': 42}
        validated = tool.validate_parameters(params)
        
        assert validated == {'required_param': 'test_value', 'optional_param': 42}
    
    def test_validate_parameters_missing_required(self):
        tool = MockTool()
        params = {'optional_param': 42}
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: required_param"):
            tool.validate_parameters(params)
    
    def test_validate_parameters_invalid_type(self):
        tool = MockTool()
        params = {'required_param': 'test', 'optional_param': 'not_an_int'}
        
        with pytest.raises(ToolValidationError, match="optional_param must be an integer"):
            tool.validate_parameters(params)
    
    def test_validate_parameters_not_dict(self):
        tool = MockTool()
        
        with pytest.raises(ToolValidationError, match="Parameters must be a dictionary"):
            tool.validate_parameters("not_a_dict")


class TestFunctionCallValidation:
    """Test the validate_function_call method."""
    
    def test_validate_function_call_success(self):
        tool = MockTool()
        
        # Mock function call object
        function_call = Mock()
        function_call.arguments = '{"required_param": "test_value"}'
        
        validated = tool.validate_function_call(function_call)
        assert validated == {'required_param': 'test_value'}
    
    def test_validate_function_call_with_optional_params(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '{"required_param": "test", "optional_param": 42}'
        
        validated = tool.validate_function_call(function_call)
        assert validated == {'required_param': 'test', 'optional_param': 42}
    
    def test_validate_function_call_invalid_json(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '{"invalid": json}'
        
        with pytest.raises(ToolValidationError, match="Failed to parse function call arguments"):
            tool.validate_function_call(function_call)
    
    def test_validate_function_call_missing_required(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '{"optional_param": 42}'
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: required_param"):
            tool.validate_function_call(function_call)
    
    def test_validate_function_call_string_input(self):
        tool = MockTool()
        
        # Test when function_call is a string
        function_call = '{"required_param": "test_value"}'
        
        validated = tool.validate_function_call(function_call)
        assert validated == {'required_param': 'test_value'}
    
    def test_validate_function_call_validation_error_propagation(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '{"required_param": "test", "optional_param": "invalid"}'
        
        with pytest.raises(ToolValidationError, match="optional_param must be an integer"):
            tool.validate_function_call(function_call)


class TestToolAbstractMethods:
    """Test that Tool is properly abstract."""
    
    def test_cannot_instantiate_base_tool(self):
        with pytest.raises(TypeError, match="Can't instantiate abstract class Tool"):
            Tool("test", "description")
    
    def test_must_implement_get_schema(self):
        class IncompleteToolNoSchema(Tool):
            def validate_parameters(self, parameters):
                return parameters
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteToolNoSchema("test", "description")
    
    def test_must_implement_validate_parameters(self):
        class IncompleteToolNoValidation(Tool):
            def get_schema(self, use_short_description=False):
                return {}
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteToolNoValidation("test", "description")


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_json_arguments(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '{}'
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: required_param"):
            tool.validate_function_call(function_call)
    
    def test_null_arguments(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = 'null'
        
        with pytest.raises(ToolValidationError, match="Parameters must be a dictionary"):
            tool.validate_function_call(function_call)
    
    def test_array_arguments(self):
        tool = MockTool()
        
        function_call = Mock()
        function_call.arguments = '["not", "a", "dict"]'
        
        with pytest.raises(ToolValidationError, match="Parameters must be a dictionary"):
            tool.validate_function_call(function_call)
    
    def test_function_call_without_arguments_attribute(self):
        tool = MockTool()
        
        # Mock object without arguments attribute
        function_call = Mock(spec=[])  # Empty spec means no attributes
        
        # Should convert to string and try to parse
        with pytest.raises(ToolValidationError):
            tool.validate_function_call(function_call)