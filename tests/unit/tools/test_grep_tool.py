"""Tests for GrepTool - ReadOnly agent safe text searching tool."""

import pytest
from unittest.mock import Mock

from openhands.agenthub.readonly_agent.tools.unified import GrepTool
from openhands.agenthub.codeact_agent.tools.unified.base import ToolValidationError


class TestGrepToolSchema:
    """Test GrepTool schema generation."""
    
    def test_grep_tool_initialization(self):
        tool = GrepTool()
        assert tool.name == 'grep'
        assert 'grep' in tool.description.lower() or 'search' in tool.description.lower()
    
    def test_grep_tool_schema_structure(self):
        tool = GrepTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'grep'
        assert 'description' in schema['function']
        assert 'parameters' in schema['function']
        
        params = schema['function']['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'required' in params
    
    def test_grep_tool_required_parameters(self):
        tool = GrepTool()
        schema = tool.get_schema()
        
        required = schema['function']['parameters']['required']
        assert 'pattern' in required
        assert 'path' in required
        
        properties = schema['function']['parameters']['properties']
        assert 'pattern' in properties
        assert 'path' in properties
        assert properties['pattern']['type'] == 'string'
        assert properties['path']['type'] == 'string'
    
    def test_grep_tool_optional_parameters(self):
        tool = GrepTool()
        schema = tool.get_schema()
        
        properties = schema['function']['parameters']['properties']
        
        # Should have optional parameters
        optional_params = ['recursive', 'case_sensitive']
        for param in optional_params:
            if param in properties:
                assert properties[param]['type'] == 'boolean'
    
    def test_grep_tool_description_is_safe(self):
        tool = GrepTool()
        schema = tool.get_schema()
        
        description = schema['function']['description'].lower()
        
        # Should mention safe operations
        assert any(word in description for word in ['search', 'find', 'pattern', 'grep'])
        
        # Should NOT mention dangerous operations
        dangerous_words = ['edit', 'modify', 'write', 'delete', 'execute', 'run', 'create']
        assert not any(word in description for word in dangerous_words)


class TestGrepToolParameterValidation:
    """Test GrepTool parameter validation."""
    
    def test_validate_valid_parameters(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/user/'}
        
        validated = tool.validate_parameters(params)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/home/user/'
        assert validated['recursive'] is True  # Default value
        assert validated['case_sensitive'] is False  # Default value
    
    def test_validate_missing_pattern(self):
        tool = GrepTool()
        params = {'path': '/home/user/'}
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: pattern"):
            tool.validate_parameters(params)
    
    def test_validate_missing_path(self):
        tool = GrepTool()
        params = {'pattern': 'test'}
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: path"):
            tool.validate_parameters(params)
    
    def test_validate_empty_pattern(self):
        tool = GrepTool()
        params = {'pattern': '', 'path': '/home/user/'}
        
        with pytest.raises(ToolValidationError, match="Parameter 'pattern' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_empty_path(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': ''}
        
        with pytest.raises(ToolValidationError, match="Parameter 'path' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_whitespace_only_pattern(self):
        tool = GrepTool()
        params = {'pattern': '   \t\n   ', 'path': '/home/user/'}
        
        with pytest.raises(ToolValidationError, match="Parameter 'pattern' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_whitespace_only_path(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '   \t\n   '}
        
        with pytest.raises(ToolValidationError, match="Parameter 'path' cannot be empty"):
            tool.validate_parameters(params)
    
    def test_validate_pattern_not_string(self):
        tool = GrepTool()
        params = {'pattern': 123, 'path': '/home/user/'}
        
        with pytest.raises(ToolValidationError, match="Parameter 'pattern' must be a string"):
            tool.validate_parameters(params)
    
    def test_validate_path_not_string(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': 123}
        
        with pytest.raises(ToolValidationError, match="Parameter 'path' must be a string"):
            tool.validate_parameters(params)
    
    def test_validate_strips_whitespace(self):
        tool = GrepTool()
        params = {'pattern': '  test  ', 'path': '  /home/user/  '}
        
        validated = tool.validate_parameters(params)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/home/user/'
    
    def test_validate_parameters_not_dict(self):
        tool = GrepTool()
        
        with pytest.raises(ToolValidationError, match="Parameters must be a dictionary"):
            tool.validate_parameters("not a dict")


class TestGrepToolOptionalParameters:
    """Test GrepTool optional parameter validation."""
    
    def test_validate_recursive_true(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'recursive': True}
        
        validated = tool.validate_parameters(params)
        assert validated['recursive'] is True
    
    def test_validate_recursive_false(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'recursive': False}
        
        validated = tool.validate_parameters(params)
        assert validated['recursive'] is False
    
    def test_validate_recursive_not_boolean(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'recursive': 'yes'}
        
        with pytest.raises(ToolValidationError, match="Parameter 'recursive' must be a boolean"):
            tool.validate_parameters(params)
    
    def test_validate_case_sensitive_true(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'case_sensitive': True}
        
        validated = tool.validate_parameters(params)
        assert validated['case_sensitive'] is True
    
    def test_validate_case_sensitive_false(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'case_sensitive': False}
        
        validated = tool.validate_parameters(params)
        assert validated['case_sensitive'] is False
    
    def test_validate_case_sensitive_not_boolean(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/', 'case_sensitive': 'no'}
        
        with pytest.raises(ToolValidationError, match="Parameter 'case_sensitive' must be a boolean"):
            tool.validate_parameters(params)
    
    def test_validate_all_optional_parameters(self):
        tool = GrepTool()
        params = {
            'pattern': 'test',
            'path': '/home/',
            'recursive': False,
            'case_sensitive': True
        }
        
        validated = tool.validate_parameters(params)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/home/'
        assert validated['recursive'] is False
        assert validated['case_sensitive'] is True
    
    def test_validate_default_values(self):
        tool = GrepTool()
        params = {'pattern': 'test', 'path': '/home/'}
        
        validated = tool.validate_parameters(params)
        assert validated['recursive'] is True  # Default
        assert validated['case_sensitive'] is False  # Default


class TestGrepToolFunctionCallValidation:
    """Test GrepTool function call validation."""
    
    def test_function_call_valid_json(self):
        tool = GrepTool()
        
        function_call = Mock()
        function_call.arguments = '{"pattern": "test", "path": "/home/user/"}'
        
        validated = tool.validate_function_call(function_call)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/home/user/'
    
    def test_function_call_with_optional_params(self):
        tool = GrepTool()
        
        function_call = Mock()
        function_call.arguments = '{"pattern": "test", "path": "/home/", "recursive": false, "case_sensitive": true}'
        
        validated = tool.validate_function_call(function_call)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/home/'
        assert validated['recursive'] is False
        assert validated['case_sensitive'] is True
    
    def test_function_call_invalid_json(self):
        tool = GrepTool()
        
        function_call = Mock()
        function_call.arguments = '{"pattern": invalid json}'
        
        with pytest.raises(ToolValidationError, match="Failed to parse function call arguments"):
            tool.validate_function_call(function_call)
    
    def test_function_call_missing_pattern(self):
        tool = GrepTool()
        
        function_call = Mock()
        function_call.arguments = '{"path": "/home/"}'
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: pattern"):
            tool.validate_function_call(function_call)
    
    def test_function_call_missing_path(self):
        tool = GrepTool()
        
        function_call = Mock()
        function_call.arguments = '{"pattern": "test"}'
        
        with pytest.raises(ToolValidationError, match="Missing required parameter: path"):
            tool.validate_function_call(function_call)


class TestGrepToolEdgeCases:
    """Test GrepTool edge cases and error conditions."""
    
    def test_various_pattern_formats(self):
        tool = GrepTool()
        
        valid_patterns = [
            'simple',
            'with spaces',
            'with-dashes',
            'with_underscores',
            'with.dots',
            'with123numbers',
            'UPPERCASE',
            'MixedCase',
            'special!@#$%^&*()',
            'regex.*pattern',
            '^start.*end$',
            '[a-z]+',
            '\\d{3}-\\d{3}-\\d{4}'
        ]
        
        for pattern in valid_patterns:
            params = {'pattern': pattern, 'path': '/test/'}
            validated = tool.validate_parameters(params)
            assert validated['pattern'] == pattern
    
    def test_various_path_formats(self):
        tool = GrepTool()
        
        valid_paths = [
            '/absolute/path/',
            './relative/path/',
            '../parent/path/',
            'simple_dir',
            '/path/with spaces/',
            '/path/with-dashes/',
            '/path/with_underscores/',
            '/path/with.dots/',
            'single_file.txt',
            '/path/to/file.ext'
        ]
        
        for path in valid_paths:
            params = {'pattern': 'test', 'path': path}
            validated = tool.validate_parameters(params)
            assert validated['path'] == path
    
    def test_unicode_patterns_and_paths(self):
        tool = GrepTool()
        
        unicode_cases = [
            {'pattern': '测试', 'path': '/home/用户/'},
            {'pattern': 'тест', 'path': '/home/пользователь/'},
            {'pattern': 'テスト', 'path': '/home/ユーザー/'},
            {'pattern': 'prueba', 'path': '/home/usuario/'}
        ]
        
        for case in unicode_cases:
            validated = tool.validate_parameters(case)
            assert validated['pattern'] == case['pattern']
            assert validated['path'] == case['path']
    
    def test_very_long_pattern(self):
        tool = GrepTool()
        
        # Very long pattern
        long_pattern = 'test' * 1000
        params = {'pattern': long_pattern, 'path': '/test/'}
        
        validated = tool.validate_parameters(params)
        assert validated['pattern'] == long_pattern
    
    def test_very_long_path(self):
        tool = GrepTool()
        
        # Very long path
        long_path = '/very/long/path/' + 'directory/' * 100
        params = {'pattern': 'test', 'path': long_path}
        
        validated = tool.validate_parameters(params)
        assert validated['path'] == long_path


class TestGrepToolSafety:
    """Test GrepTool safety characteristics."""
    
    def test_grep_tool_is_read_only(self):
        """Test that GrepTool is recognized as a read-only tool."""
        tool = GrepTool()
        schema = tool.get_schema()
        
        description = schema['function']['description'].lower()
        
        # Should indicate search operations
        assert any(word in description for word in ['search', 'find', 'pattern', 'grep'])
        
        # Should NOT indicate modification operations
        dangerous_words = ['edit', 'modify', 'write', 'delete', 'execute', 'run', 'create']
        assert not any(word in description for word in dangerous_words)
    
    def test_grep_tool_allows_safe_operations(self):
        """Test that GrepTool allows safe search operations."""
        tool = GrepTool()
        
        safe_operations = [
            {'pattern': 'function', 'path': '/project/src/'},
            {'pattern': 'TODO', 'path': '/project/'},
            {'pattern': 'import', 'path': '/project/'},
            {'pattern': 'class.*Test', 'path': '/project/tests/'},
            {'pattern': 'def main', 'path': '/project/'}
        ]
        
        for params in safe_operations:
            validated = tool.validate_parameters(params)
            assert validated['pattern'] == params['pattern']
            assert validated['path'] == params['path']
    
    def test_grep_tool_parameter_types(self):
        """Test that GrepTool handles parameter types correctly."""
        tool = GrepTool()
        
        # Test with different parameter combinations
        test_cases = [
            {'pattern': 'test', 'path': '/home/'},
            {'pattern': 'test', 'path': '/home/', 'recursive': True},
            {'pattern': 'test', 'path': '/home/', 'case_sensitive': False},
            {'pattern': 'test', 'path': '/home/', 'recursive': False, 'case_sensitive': True},
        ]
        
        for params in test_cases:
            validated = tool.validate_parameters(params)
            assert 'pattern' in validated
            assert 'path' in validated
            assert isinstance(validated['pattern'], str)
            assert isinstance(validated['path'], str)
            assert isinstance(validated['recursive'], bool)
            assert isinstance(validated['case_sensitive'], bool)