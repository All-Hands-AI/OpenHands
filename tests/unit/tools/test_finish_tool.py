"""Tests for FinishTool - task completion tool used by multiple agents."""

import pytest
from unittest.mock import Mock

from openhands.agenthub.codeact_agent.tools.unified import FinishTool
from openhands.agenthub.codeact_agent.tools.unified.base import ToolValidationError


class TestFinishToolSchema:
    """Test FinishTool schema generation."""
    
    def test_finish_tool_initialization(self):
        tool = FinishTool()
        assert tool.name == 'finish'
        assert 'finish' in tool.description.lower() or 'complete' in tool.description.lower()
    
    def test_finish_tool_schema_structure(self):
        tool = FinishTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'finish'
        assert 'description' in schema['function']
        assert 'parameters' in schema['function']
        
        params = schema['function']['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'required' in params
    
    def test_finish_tool_required_parameters(self):
        tool = FinishTool()
        schema = tool.get_schema()
        
        required = schema['function']['parameters']['required']
        assert 'message' in required
        
        properties = schema['function']['parameters']['properties']
        assert 'message' in properties
        assert properties['message']['type'] == 'string'
    
    def test_finish_tool_description_content(self):
        tool = FinishTool()
        schema = tool.get_schema()
        
        description = schema['function']['description'].lower()
        
        # Should mention completion/finishing
        assert any(word in description for word in ['finish', 'complete', 'done', 'end', 'task'])


class TestFinishToolParameterValidation:
    """Test FinishTool parameter validation."""
    
    def test_validate_valid_message(self):
        tool = FinishTool()
        params = {'message': 'Task completed successfully'}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == 'Task completed successfully'
    
    def test_validate_missing_message(self):
        tool = FinishTool()
        params = {}
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: message"):
            tool.validate_parameters(params)
    
    def test_validate_empty_message(self):
        tool = FinishTool()
        params = {'message': ''}
        
        with pytest.raises(ToolValidationError, match="Parameter 'message' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_whitespace_only_message(self):
        tool = FinishTool()
        params = {'message': '   \t\n   '}
        
        with pytest.raises(ToolValidationError, match="Parameter 'message' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_message_not_string(self):
        tool = FinishTool()
        params = {'message': 123}
        
        with pytest.raises(ToolValidationError, match="Parameter 'message' must be a string"):
            tool.validate_parameters(params)
    
    def test_validate_message_strips_whitespace(self):
        tool = FinishTool()
        params = {'message': '  Task completed  '}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == 'Task completed'
    
    def test_validate_parameters_not_dict(self):
        tool = FinishTool()
        
        with pytest.raises(ToolValidationError, match="Parameters must be a dictionary"):
            tool.validate_parameters("not a dict")
    
    def test_validate_with_optional_parameters(self):
        tool = FinishTool()
        params = {
            'message': 'Task completed',
            'task_completed': True
        }
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == 'Task completed'
        
        # Optional parameters should be included if present and valid
        if 'task_completed' in validated:
            assert isinstance(validated['task_completed'], (bool, str))


class TestFinishToolFunctionCallValidation:
    """Test FinishTool function call validation."""
    
    def test_function_call_valid_json(self):
        tool = FinishTool()
        
        function_call = Mock()
        function_call.arguments = '{"message": "Task completed successfully"}'
        
        validated = tool.validate_function_call(function_call)
        assert validated['message'] == 'Task completed successfully'
    
    def test_function_call_invalid_json(self):
        tool = FinishTool()
        
        function_call = Mock()
        function_call.arguments = '{"message": invalid json}'
        
        with pytest.raises(ToolValidationError, match="Failed to parse function call arguments"):
            tool.validate_function_call(function_call)
    
    def test_function_call_missing_message(self):
        tool = FinishTool()
        
        function_call = Mock()
        function_call.arguments = '{"task_completed": true}'
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: message"):
            tool.validate_function_call(function_call)
    
    def test_function_call_complex_message(self):
        tool = FinishTool()
        
        complex_message = 'Task completed successfully!\n\nSummary:\n- Created 5 files\n- Fixed 3 bugs\n- Added tests'
        function_call = Mock()
        function_call.arguments = f'{{"message": "{complex_message}"}}'
        
        validated = tool.validate_function_call(function_call)
        assert validated['message'] == complex_message


class TestFinishToolEdgeCases:
    """Test FinishTool edge cases and error conditions."""
    
    def test_very_long_message(self):
        tool = FinishTool()
        
        # Very long message
        long_message = 'Task completed! ' + 'Details: ' * 1000
        params = {'message': long_message}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == long_message
    
    def test_message_with_special_characters(self):
        tool = FinishTool()
        
        special_message = 'Task completed! ✅ Success rate: 100% 🎉'
        params = {'message': special_message}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == special_message
    
    def test_message_with_newlines(self):
        tool = FinishTool()
        
        multiline_message = 'Task completed!\nAll tests passed.\nReady for deployment.'
        params = {'message': multiline_message}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == multiline_message
    
    def test_message_with_unicode(self):
        tool = FinishTool()
        
        unicode_message = 'Tarea completada! 任务完成! タスク完了! Задача выполнена!'
        params = {'message': unicode_message}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == unicode_message
    
    def test_message_with_json_content(self):
        tool = FinishTool()
        
        json_message = 'Task completed with result: {"status": "success", "count": 42}'
        params = {'message': json_message}
        
        validated = tool.validate_parameters(params)
        assert validated['message'] == json_message


class TestFinishToolUsagePatterns:
    """Test common usage patterns for FinishTool."""
    
    def test_success_message(self):
        tool = FinishTool()
        
        success_messages = [
            'Task completed successfully',
            'All requirements have been implemented',
            'Bug fixed and tests added',
            'Feature development complete',
            'Code review completed - all issues resolved'
        ]
        
        for message in success_messages:
            params = {'message': message}
            validated = tool.validate_parameters(params)
            assert validated['message'] == message
    
    def test_failure_message(self):
        tool = FinishTool()
        
        failure_messages = [
            'Unable to complete task due to missing dependencies',
            'Task failed: insufficient permissions',
            'Cannot proceed: required files not found',
            'Task incomplete: external service unavailable'
        ]
        
        for message in failure_messages:
            params = {'message': message}
            validated = tool.validate_parameters(params)
            assert validated['message'] == message
    
    def test_partial_completion_message(self):
        tool = FinishTool()
        
        partial_messages = [
            'Task partially completed - 3 of 5 items done',
            'Progress update: 80% complete, remaining work identified',
            'Milestone reached - ready for next phase'
        ]
        
        for message in partial_messages:
            params = {'message': message}
            validated = tool.validate_parameters(params)
            assert validated['message'] == message


class TestFinishToolInheritance:
    """Test FinishTool inheritance by ReadOnly agent."""
    
    def test_finish_tool_available_in_readonly(self):
        """Test that FinishTool can be imported from ReadOnly agent."""
        from openhands.agenthub.readonly_agent.tools.unified import FinishTool as ReadOnlyFinish
        from openhands.agenthub.codeact_agent.tools.unified import FinishTool as CodeActFinish
        
        # Should be the same class
        assert ReadOnlyFinish is CodeActFinish
    
    def test_finish_tool_works_same_in_both_agents(self):
        """Test that FinishTool works identically in both agents."""
        from openhands.agenthub.readonly_agent.tools.unified import FinishTool as ReadOnlyFinish
        from openhands.agenthub.codeact_agent.tools.unified import FinishTool as CodeActFinish
        
        readonly_tool = ReadOnlyFinish()
        codeact_tool = CodeActFinish()
        
        # Same schema
        assert readonly_tool.get_schema() == codeact_tool.get_schema()
        
        # Same validation
        params = {'message': 'Test message'}
        readonly_validated = readonly_tool.validate_parameters(params)
        codeact_validated = codeact_tool.validate_parameters(params)
        assert readonly_validated == codeact_validated


class TestFinishToolSafety:
    """Test FinishTool safety characteristics."""
    
    def test_finish_tool_is_safe(self):
        """Test that FinishTool is safe for all agents."""
        tool = FinishTool()
        schema = tool.get_schema()
        
        description = schema['function']['description'].lower()
        
        # Should indicate completion/finishing
        assert any(word in description for word in ['finish', 'complete', 'done', 'end'])
        
        # Should NOT indicate dangerous operations
        dangerous_words = ['execute', 'run', 'delete', 'modify', 'write']
        assert not any(word in description for word in dangerous_words)
    
    def test_finish_tool_parameter_types(self):
        """Test that FinishTool handles parameter types correctly."""
        tool = FinishTool()
        
        # Test with different message types
        test_cases = [
            {'message': 'Simple message'},
            {'message': 'Message with numbers: 123'},
            {'message': 'Message with symbols: !@#$%'},
        ]
        
        for params in test_cases:
            validated = tool.validate_parameters(params)
            assert 'message' in validated
            assert isinstance(validated['message'], str)