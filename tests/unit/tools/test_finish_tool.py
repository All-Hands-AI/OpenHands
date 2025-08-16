"""Tests for FinishTool - task completion tool used by multiple agents."""

from unittest.mock import Mock

import pytest

from openhands.agenthub.codeact_agent.tools.finish_tool import FinishTool
from openhands.core.exceptions import FunctionCallValidationError as ToolValidationError


class TestFinishToolSchema:
    """Test FinishTool schema generation."""

    def test_finish_tool_initialization(self):
        tool = FinishTool()
        assert tool.name == 'finish'
        assert (
            'finish' in tool.description.lower()
            or 'complete' in tool.description.lower()
        )

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
        assert required == []  # No required parameters

        properties = schema['function']['parameters']['properties']
        assert 'outputs' in properties
        assert 'summary' in properties
        assert properties['outputs']['type'] == 'object'
        assert properties['summary']['type'] == 'string'

    def test_finish_tool_description_content(self):
        tool = FinishTool()
        schema = tool.get_schema()

        description = schema['function']['description'].lower()

        # Should mention completion/finishing
        assert any(
            word in description
            for word in ['finish', 'complete', 'done', 'end', 'task']
        )


class TestFinishToolParameterValidation:
    """Test FinishTool parameter validation."""

    def test_validate_valid_summary(self):
        tool = FinishTool()
        params = {'summary': 'Task completed successfully'}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == 'Task completed successfully'

    def test_validate_empty_parameters(self):
        tool = FinishTool()
        params = {}

        # Should not raise error - no required parameters
        validated = tool.validate_parameters(params)
        assert validated == {}

    def test_validate_valid_outputs(self):
        tool = FinishTool()
        params = {'outputs': {'result': 'success', 'count': 42}}

        validated = tool.validate_parameters(params)
        assert validated['outputs'] == {'result': 'success', 'count': 42}

    def test_validate_outputs_not_dict(self):
        tool = FinishTool()
        params = {'outputs': 'not a dict'}

        with pytest.raises(ToolValidationError, match="'outputs' must be a dictionary"):
            tool.validate_parameters(params)

    def test_validate_summary_conversion(self):
        tool = FinishTool()
        params = {'summary': 123}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == '123'

    def test_validate_both_parameters(self):
        tool = FinishTool()
        params = {'outputs': {'status': 'done'}, 'summary': 'Task completed'}

        validated = tool.validate_parameters(params)
        assert validated['outputs'] == {'status': 'done'}
        assert validated['summary'] == 'Task completed'

    def test_validate_parameters_not_dict(self):
        tool = FinishTool()

        # FinishTool doesn't validate parameter type - just ignores invalid ones
        validated = tool.validate_parameters('not a dict')
        assert validated == {}

    def test_validate_with_unknown_parameters(self):
        tool = FinishTool()
        params = {'summary': 'Task completed', 'unknown_param': 'ignored'}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == 'Task completed'

        # Unknown parameters should be ignored
        assert 'unknown_param' not in validated


class TestFinishToolFunctionCallValidation:
    """Test FinishTool function call validation."""

    def test_function_call_valid_json(self):
        tool = FinishTool()

        function_call = Mock()
        function_call.arguments = '{"summary": "Task completed successfully"}'

        validated = tool.validate_function_call(function_call)
        assert validated['summary'] == 'Task completed successfully'

    def test_function_call_invalid_json(self):
        tool = FinishTool()

        function_call = Mock()
        function_call.arguments = '{"message": invalid json}'

        with pytest.raises(
            ToolValidationError, match='Failed to parse function call arguments'
        ):
            tool.validate_function_call(function_call)

    def test_function_call_empty_parameters(self):
        tool = FinishTool()

        function_call = Mock()
        function_call.arguments = '{}'

        # Should not raise error - no required parameters
        validated = tool.validate_function_call(function_call)
        assert validated == {}

    def test_function_call_complex_outputs(self):
        tool = FinishTool()

        function_call = Mock()
        function_call.arguments = '{"outputs": {"files_created": 5, "bugs_fixed": 3}, "summary": "Task completed successfully"}'

        validated = tool.validate_function_call(function_call)
        assert validated['outputs'] == {'files_created': 5, 'bugs_fixed': 3}
        assert validated['summary'] == 'Task completed successfully'


class TestFinishToolEdgeCases:
    """Test FinishTool edge cases and error conditions."""

    def test_very_long_summary(self):
        tool = FinishTool()

        # Very long summary
        long_summary = 'Task completed! ' + 'Details: ' * 1000
        params = {'summary': long_summary}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == long_summary

    def test_summary_with_special_characters(self):
        tool = FinishTool()

        special_summary = 'Task completed! ✅ Success rate: 100% 🎉'
        params = {'summary': special_summary}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == special_summary

    def test_summary_with_newlines(self):
        tool = FinishTool()

        multiline_summary = 'Task completed!\nAll tests passed.\nReady for deployment.'
        params = {'summary': multiline_summary}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == multiline_summary

    def test_summary_with_unicode(self):
        tool = FinishTool()

        unicode_summary = 'Tarea completada! 任务完成! タスク完了! Задача выполнена!'
        params = {'summary': unicode_summary}

        validated = tool.validate_parameters(params)
        assert validated['summary'] == unicode_summary

    def test_complex_outputs_structure(self):
        tool = FinishTool()

        complex_outputs = {
            'status': 'success',
            'results': {'count': 42, 'items': ['a', 'b', 'c']},
            'metadata': {'timestamp': '2024-01-01', 'version': '1.0'},
        }
        params = {'outputs': complex_outputs}

        validated = tool.validate_parameters(params)
        assert validated['outputs'] == complex_outputs


class TestFinishToolUsagePatterns:
    """Test common usage patterns for FinishTool."""

    def test_success_patterns(self):
        tool = FinishTool()

        success_cases = [
            {
                'summary': 'Task completed successfully',
                'outputs': {'status': 'success'},
            },
            {'summary': 'All requirements implemented', 'outputs': {'features': 5}},
            {
                'summary': 'Bug fixed and tests added',
                'outputs': {'bugs_fixed': 1, 'tests_added': 3},
            },
        ]

        for params in success_cases:
            validated = tool.validate_parameters(params)
            assert validated['summary'] == params['summary']
            assert validated['outputs'] == params['outputs']

    def test_failure_patterns(self):
        tool = FinishTool()

        failure_cases = [
            {
                'summary': 'Unable to complete task',
                'outputs': {'status': 'failed', 'reason': 'missing deps'},
            },
            {'summary': 'Task failed: permissions', 'outputs': {'status': 'error'}},
        ]

        for params in failure_cases:
            validated = tool.validate_parameters(params)
            assert validated['summary'] == params['summary']
            assert validated['outputs'] == params['outputs']

    def test_partial_completion_patterns(self):
        tool = FinishTool()

        partial_cases = [
            {'summary': 'Partial completion', 'outputs': {'completed': 3, 'total': 5}},
            {'summary': '80% complete', 'outputs': {'progress': 0.8}},
        ]

        for params in partial_cases:
            validated = tool.validate_parameters(params)
            assert validated['summary'] == params['summary']
            assert validated['outputs'] == params['outputs']


class TestFinishToolInheritance:
    """Test FinishTool inheritance by ReadOnly agent."""

    def test_finish_tool_available_in_readonly(self):
        """Test that FinishTool can be imported from ReadOnly agent."""
        from openhands.agenthub.codeact_agent.tools.unified import (
            FinishTool as CodeActFinish,
        )
        from openhands.agenthub.readonly_agent.tools.unified import (
            FinishTool as ReadOnlyFinish,
        )

        # Should be the same class
        assert ReadOnlyFinish is CodeActFinish

    def test_finish_tool_works_same_in_both_agents(self):
        """Test that FinishTool works identically in both agents."""
        from openhands.agenthub.codeact_agent.tools.unified import (
            FinishTool as CodeActFinish,
        )
        from openhands.agenthub.readonly_agent.tools.unified import (
            FinishTool as ReadOnlyFinish,
        )

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
        assert any(
            word in description for word in ['finish', 'complete', 'done', 'end']
        )

        # Should NOT indicate dangerous operations
        dangerous_words = ['execute', 'run', 'delete', 'modify', 'write']
        assert not any(word in description for word in dangerous_words)

    def test_finish_tool_parameter_types(self):
        """Test that FinishTool handles parameter types correctly."""
        tool = FinishTool()

        # Test with different parameter types
        test_cases = [
            {'summary': 'Simple summary'},
            {'outputs': {'count': 123}},
            {'summary': 'Summary with symbols: !@#$%', 'outputs': {'status': 'done'}},
        ]

        for params in test_cases:
            validated = tool.validate_parameters(params)
            if 'summary' in params:
                assert 'summary' in validated
                assert isinstance(validated['summary'], str)
            if 'outputs' in params:
                assert 'outputs' in validated
                assert isinstance(validated['outputs'], dict)
