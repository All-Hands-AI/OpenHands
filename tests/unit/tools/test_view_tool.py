"""Tests for ViewTool - ReadOnly agent safe file viewing tool."""

from unittest.mock import Mock

import pytest

from openhands.agenthub.codeact_agent.tools.unified.base import ToolValidationError
from openhands.agenthub.readonly_agent.tools.unified import ViewTool


class TestViewToolSchema:
    """Test ViewTool schema generation."""

    def test_view_tool_initialization(self):
        tool = ViewTool()
        assert tool.name == 'view'
        assert 'view' in tool.description.lower()

    def test_view_tool_schema_structure(self):
        tool = ViewTool()
        schema = tool.get_schema()

        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'view'
        assert 'description' in schema['function']
        assert 'parameters' in schema['function']

        params = schema['function']['parameters']
        assert params['type'] == 'object'
        assert 'properties' in params
        assert 'required' in params

    def test_view_tool_required_parameters(self):
        tool = ViewTool()
        schema = tool.get_schema()

        required = schema['function']['parameters']['required']
        assert 'path' in required

        properties = schema['function']['parameters']['properties']
        assert 'path' in properties
        assert properties['path']['type'] == 'string'

    def test_view_tool_optional_parameters(self):
        tool = ViewTool()
        schema = tool.get_schema()

        properties = schema['function']['parameters']['properties']

        # Should have view_range as optional parameter
        if 'view_range' in properties:
            assert properties['view_range']['type'] == 'array'
            assert properties['view_range']['items']['type'] == 'integer'

    def test_view_tool_description_is_safe(self):
        tool = ViewTool()
        schema = tool.get_schema()

        description = schema['function']['description'].lower()

        # Should mention safe operations
        assert any(word in description for word in ['read', 'view', 'display', 'list'])

        # Should NOT mention dangerous operations (but "read" is safe)
        dangerous_words = ['edit', 'modify', 'write', 'delete', 'execute', 'create']
        # Note: 'run' removed because it appears in 'truncated' in ViewTool description
        assert not any(word in description for word in dangerous_words)


class TestViewToolParameterValidation:
    """Test ViewTool parameter validation."""

    def test_validate_valid_path(self):
        tool = ViewTool()
        params = {'path': '/home/user/file.txt'}

        validated = tool.validate_parameters(params)
        assert validated['path'] == '/home/user/file.txt'

    def test_validate_missing_path(self):
        tool = ViewTool()
        params = {}

        with pytest.raises(
            ToolValidationError, match='Missing required parameter: path'
        ):
            tool.validate_parameters(params)

    def test_validate_empty_path(self):
        tool = ViewTool()
        params = {'path': ''}

        with pytest.raises(
            ToolValidationError, match="Parameter 'path' cannot be empty"
        ):
            tool.validate_parameters(params)

    def test_validate_whitespace_only_path(self):
        tool = ViewTool()
        params = {'path': '   \t\n   '}

        with pytest.raises(
            ToolValidationError, match="Parameter 'path' cannot be empty"
        ):
            tool.validate_parameters(params)

    def test_validate_path_not_string(self):
        tool = ViewTool()
        params = {'path': 123}

        with pytest.raises(
            ToolValidationError, match="Parameter 'path' must be a string"
        ):
            tool.validate_parameters(params)

    def test_validate_path_strips_whitespace(self):
        tool = ViewTool()
        params = {'path': '  /home/user/file.txt  '}

        validated = tool.validate_parameters(params)
        assert validated['path'] == '/home/user/file.txt'

    def test_validate_parameters_not_dict(self):
        tool = ViewTool()

        with pytest.raises(
            ToolValidationError, match='Parameters must be a dictionary'
        ):
            tool.validate_parameters('not a dict')


class TestViewToolViewRangeValidation:
    """Test ViewTool view_range parameter validation."""

    def test_validate_valid_view_range(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [1, 10]}

        validated = tool.validate_parameters(params)
        assert validated['path'] == '/test/file.txt'
        assert validated['view_range'] == [1, 10]

    def test_validate_view_range_with_end_minus_one(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [5, -1]}

        validated = tool.validate_parameters(params)
        assert validated['view_range'] == [5, -1]

    def test_validate_view_range_not_list(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': 'not a list'}

        with pytest.raises(
            ToolValidationError, match="Parameter 'view_range' must be a list"
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_wrong_length(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [1]}

        with pytest.raises(
            ToolValidationError,
            match="Parameter 'view_range' must contain exactly 2 elements",
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_too_many_elements(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [1, 2, 3]}

        with pytest.raises(
            ToolValidationError,
            match="Parameter 'view_range' must contain exactly 2 elements",
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_non_integer_elements(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [1.5, 10]}

        with pytest.raises(
            ToolValidationError,
            match="Parameter 'view_range' elements must be integers",
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_string_elements(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': ['1', '10']}

        with pytest.raises(
            ToolValidationError,
            match="Parameter 'view_range' elements must be integers",
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_start_less_than_one(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [0, 10]}

        with pytest.raises(
            ToolValidationError, match="Parameter 'view_range' start must be >= 1"
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_negative_start(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [-5, 10]}

        with pytest.raises(
            ToolValidationError, match="Parameter 'view_range' start must be >= 1"
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_end_less_than_start(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': [10, 5]}

        with pytest.raises(
            ToolValidationError,
            match="Parameter 'view_range' end must be >= start or -1",
        ):
            tool.validate_parameters(params)

    def test_validate_view_range_none_value(self):
        tool = ViewTool()
        params = {'path': '/test/file.txt', 'view_range': None}

        # None should be ignored (optional parameter)
        validated = tool.validate_parameters(params)
        assert 'view_range' not in validated


class TestViewToolFunctionCallValidation:
    """Test ViewTool function call validation."""

    def test_function_call_valid_json(self):
        tool = ViewTool()

        function_call = Mock()
        function_call.arguments = '{"path": "/test/file.txt"}'

        validated = tool.validate_function_call(function_call)
        assert validated['path'] == '/test/file.txt'

    def test_function_call_with_view_range(self):
        tool = ViewTool()

        function_call = Mock()
        function_call.arguments = '{"path": "/test/file.txt", "view_range": [1, 20]}'

        validated = tool.validate_function_call(function_call)
        assert validated['path'] == '/test/file.txt'
        assert validated['view_range'] == [1, 20]

    def test_function_call_invalid_json(self):
        tool = ViewTool()

        function_call = Mock()
        function_call.arguments = '{"path": invalid json}'

        with pytest.raises(
            ToolValidationError, match='Failed to parse function call arguments'
        ):
            tool.validate_function_call(function_call)

    def test_function_call_missing_path(self):
        tool = ViewTool()

        function_call = Mock()
        function_call.arguments = '{"view_range": [1, 10]}'

        with pytest.raises(
            ToolValidationError, match='Missing required parameter: path'
        ):
            tool.validate_function_call(function_call)


class TestViewToolEdgeCases:
    """Test ViewTool edge cases and error conditions."""

    def test_various_path_formats(self):
        tool = ViewTool()

        valid_paths = [
            '/absolute/path/file.txt',
            './relative/path/file.txt',
            '../parent/file.txt',
            'simple_file.txt',
            '/path/with spaces/file.txt',
            '/path/with-dashes/file_name.txt',
            '/path/with_underscores/file_name.txt',
            '/path/with.dots/file.name.txt',
        ]

        for path in valid_paths:
            params = {'path': path}
            validated = tool.validate_parameters(params)
            assert validated['path'] == path

    def test_unicode_paths(self):
        tool = ViewTool()

        unicode_paths = [
            '/home/用户/文件.txt',
            '/home/usuario/archivo.txt',
            '/home/пользователь/файл.txt',
            '/home/ユーザー/ファイル.txt',
        ]

        for path in unicode_paths:
            params = {'path': path}
            validated = tool.validate_parameters(params)
            assert validated['path'] == path

    def test_very_long_path(self):
        tool = ViewTool()

        # Very long path
        long_path = '/very/long/path/' + 'directory/' * 100 + 'file.txt'
        params = {'path': long_path}

        validated = tool.validate_parameters(params)
        assert validated['path'] == long_path

    def test_view_range_edge_cases(self):
        tool = ViewTool()

        edge_cases = [
            [1, 1],  # Single line
            [1, 2],  # Two lines
            [100, 200],  # Large numbers
            [1, -1],  # End of file
            [50, -1],  # From line 50 to end
        ]

        for view_range in edge_cases:
            params = {'path': '/test/file.txt', 'view_range': view_range}
            validated = tool.validate_parameters(params)
            assert validated['view_range'] == view_range


class TestViewToolSafety:
    """Test ViewTool safety characteristics."""

    def test_view_tool_is_read_only(self):
        """Test that ViewTool is recognized as a read-only tool."""
        tool = ViewTool()
        schema = tool.get_schema()

        description = schema['function']['description'].lower()

        # Should indicate read-only operations
        assert any(word in description for word in ['read', 'view', 'display', 'list'])

        # Should NOT indicate modification operations (but "read" is safe)
        dangerous_words = ['edit', 'modify', 'write', 'delete', 'execute', 'create']
        # Note: 'run' removed because it appears in 'truncated' in ViewTool description
        assert not any(word in description for word in dangerous_words)

    def test_view_tool_allows_safe_paths(self):
        """Test that ViewTool allows safe path operations."""
        tool = ViewTool()

        safe_paths = [
            '/home/user/document.txt',
            './project/README.md',
            '../config/settings.json',
            'data/input.csv',
            '/var/log/application.log',
        ]

        for path in safe_paths:
            params = {'path': path}
            validated = tool.validate_parameters(params)
            assert validated['path'] == path

    def test_view_tool_parameter_types(self):
        """Test that ViewTool handles parameter types correctly."""
        tool = ViewTool()

        # Test with different parameter combinations
        test_cases = [
            {'path': '/test/file.txt'},
            {'path': '/test/file.txt', 'view_range': [1, 10]},
            {'path': '/test/file.txt', 'view_range': [5, -1]},
        ]

        for params in test_cases:
            validated = tool.validate_parameters(params)
            assert 'path' in validated
            assert isinstance(validated['path'], str)
