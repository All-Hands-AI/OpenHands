"""Tests for LocAgent-specific tools."""

import pytest

from openhands.agenthub.codeact_agent.tools.unified.base import ToolValidationError
from openhands.agenthub.loc_agent.tools.unified import (
    ExploreStructureTool,
    SearchEntityTool,
    SearchRepoTool,
)


class TestSearchEntityTool:
    """Test SearchEntityTool schema and validation."""
    
    def test_get_schema(self):
        tool = SearchEntityTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'get_entity_contents'
        assert 'entity_names' in schema['function']['parameters']['properties']
        assert schema['function']['parameters']['required'] == ['entity_names']
    
    def test_validate_parameters_valid(self):
        tool = SearchEntityTool()
        params = {
            'entity_names': ['src/file.py:Class.method', 'src/other.py']
        }
        
        validated = tool.validate_parameters(params)
        assert validated['entity_names'] == ['src/file.py:Class.method', 'src/other.py']
    
    def test_validate_parameters_missing_entity_names(self):
        tool = SearchEntityTool()
        
        with pytest.raises(ToolValidationError, match="Missing required parameter 'entity_names'"):
            tool.validate_parameters({})
    
    def test_validate_parameters_entity_names_not_list(self):
        tool = SearchEntityTool()
        
        with pytest.raises(ToolValidationError, match="Parameter 'entity_names' must be a list"):
            tool.validate_parameters({'entity_names': 'not a list'})
    
    def test_validate_parameters_empty_entity_name(self):
        tool = SearchEntityTool()
        
        with pytest.raises(ToolValidationError, match="Entity name at index 0 cannot be empty"):
            tool.validate_parameters({'entity_names': ['']})
    
    def test_validate_parameters_non_string_entity_name(self):
        tool = SearchEntityTool()
        
        with pytest.raises(ToolValidationError, match="Entity name at index 1 must be a string"):
            tool.validate_parameters({'entity_names': ['valid', 123]})
    
    def test_validate_parameters_strips_whitespace(self):
        tool = SearchEntityTool()
        params = {
            'entity_names': ['  src/file.py:Class.method  ', '  src/other.py  ']
        }
        
        validated = tool.validate_parameters(params)
        assert validated['entity_names'] == ['src/file.py:Class.method', 'src/other.py']


class TestSearchRepoTool:
    """Test SearchRepoTool schema and validation."""
    
    def test_get_schema(self):
        tool = SearchRepoTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'search_code_snippets'
        assert 'search_terms' in schema['function']['parameters']['properties']
        assert 'line_nums' in schema['function']['parameters']['properties']
        assert 'file_path_or_pattern' in schema['function']['parameters']['properties']
        assert schema['function']['parameters']['required'] == []
    
    def test_validate_parameters_with_search_terms(self):
        tool = SearchRepoTool()
        params = {
            'search_terms': ['function', 'class'],
            'file_path_or_pattern': '**/*.py'
        }
        
        validated = tool.validate_parameters(params)
        assert validated['search_terms'] == ['function', 'class']
        assert validated['file_path_or_pattern'] == '**/*.py'
    
    def test_validate_parameters_with_line_nums(self):
        tool = SearchRepoTool()
        params = {
            'line_nums': [10, 20],
            'file_path_or_pattern': 'src/file.py'
        }
        
        validated = tool.validate_parameters(params)
        assert validated['line_nums'] == [10, 20]
        assert validated['file_path_or_pattern'] == 'src/file.py'
    
    def test_validate_parameters_default_file_pattern(self):
        tool = SearchRepoTool()
        params = {'search_terms': ['test']}
        
        validated = tool.validate_parameters(params)
        assert validated['file_path_or_pattern'] == '**/*.py'
    
    def test_validate_parameters_missing_both_search_and_line(self):
        tool = SearchRepoTool()
        
        with pytest.raises(ToolValidationError, match="Either 'search_terms' or 'line_nums' must be provided"):
            tool.validate_parameters({})
    
    def test_validate_parameters_line_nums_with_default_pattern(self):
        tool = SearchRepoTool()
        
        with pytest.raises(ToolValidationError, match="When 'line_nums' is provided, 'file_path_or_pattern' must specify a specific file path"):
            tool.validate_parameters({'line_nums': [10]})
    
    def test_validate_parameters_invalid_line_number(self):
        tool = SearchRepoTool()
        
        with pytest.raises(ToolValidationError, match="Line number at index 0 must be positive"):
            tool.validate_parameters({'line_nums': [0], 'file_path_or_pattern': 'src/file.py'})
    
    def test_validate_parameters_non_integer_line_number(self):
        tool = SearchRepoTool()
        
        with pytest.raises(ToolValidationError, match="Line number at index 0 must be an integer"):
            tool.validate_parameters({'line_nums': ['10'], 'file_path_or_pattern': 'src/file.py'})


class TestExploreStructureTool:
    """Test ExploreStructureTool schema and validation."""
    
    def test_get_schema(self):
        tool = ExploreStructureTool()
        schema = tool.get_schema()
        
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'explore_tree_structure'
        assert 'start_entities' in schema['function']['parameters']['properties']
        assert schema['function']['parameters']['required'] == ['start_entities']
    
    def test_get_schema_simplified(self):
        tool = ExploreStructureTool(use_simplified_description=True)
        schema = tool.get_schema()
        
        # Should still have the same structure but shorter description
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'explore_tree_structure'
    
    def test_validate_parameters_minimal(self):
        tool = ExploreStructureTool()
        params = {'start_entities': ['src/file.py:Class']}
        
        validated = tool.validate_parameters(params)
        assert validated['start_entities'] == ['src/file.py:Class']
        assert validated['direction'] == 'downstream'
        assert validated['traversal_depth'] == 2
    
    def test_validate_parameters_full(self):
        tool = ExploreStructureTool()
        params = {
            'start_entities': ['src/file.py:Class'],
            'direction': 'upstream',
            'traversal_depth': 5,
            'entity_type_filter': ['class', 'function'],
            'dependency_type_filter': ['imports', 'invokes']
        }
        
        validated = tool.validate_parameters(params)
        assert validated['start_entities'] == ['src/file.py:Class']
        assert validated['direction'] == 'upstream'
        assert validated['traversal_depth'] == 5
        assert validated['entity_type_filter'] == ['class', 'function']
        assert validated['dependency_type_filter'] == ['imports', 'invokes']
    
    def test_validate_parameters_missing_start_entities(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Missing required parameter 'start_entities'"):
            tool.validate_parameters({})
    
    def test_validate_parameters_empty_start_entities(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Parameter 'start_entities' cannot be empty"):
            tool.validate_parameters({'start_entities': []})
    
    def test_validate_parameters_invalid_direction(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Parameter 'direction' must be one of"):
            tool.validate_parameters({'start_entities': ['test'], 'direction': 'invalid'})
    
    def test_validate_parameters_invalid_traversal_depth(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Parameter 'traversal_depth' must be -1 or non-negative"):
            tool.validate_parameters({'start_entities': ['test'], 'traversal_depth': -2})
    
    def test_validate_parameters_invalid_entity_type(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Entity type 'invalid' is not valid"):
            tool.validate_parameters({
                'start_entities': ['test'],
                'entity_type_filter': ['invalid']
            })
    
    def test_validate_parameters_invalid_dependency_type(self):
        tool = ExploreStructureTool()
        
        with pytest.raises(ToolValidationError, match="Dependency type 'invalid' is not valid"):
            tool.validate_parameters({
                'start_entities': ['test'],
                'dependency_type_filter': ['invalid']
            })
    
    def test_validate_parameters_unlimited_depth(self):
        tool = ExploreStructureTool()
        params = {
            'start_entities': ['test'],
            'traversal_depth': -1
        }
        
        validated = tool.validate_parameters(params)
        assert validated['traversal_depth'] == -1


class TestLocAgentToolInheritance:
    """Test that LocAgent tools properly inherit from CodeAct."""
    
    def test_loc_agent_imports_codeact_tools(self):
        """Test that LocAgent can import CodeAct tools."""
        from openhands.agenthub.loc_agent.tools.unified import (
            BashTool,
            BrowserTool,
            FileEditorTool,
            FinishTool,
        )
        
        # Should be able to instantiate inherited tools
        bash_tool = BashTool()
        browser_tool = BrowserTool()
        file_tool = FileEditorTool()
        finish_tool = FinishTool()
        
        assert bash_tool.name == 'execute_bash'
        assert browser_tool.name == 'browser'
        assert file_tool.name == 'str_replace_editor'
        assert finish_tool.name == 'finish'
    
    def test_loc_agent_specific_tools(self):
        """Test that LocAgent has its own specific tools."""
        search_entity = SearchEntityTool()
        search_repo = SearchRepoTool()
        explore_structure = ExploreStructureTool()
        
        assert search_entity.name == 'get_entity_contents'
        assert search_repo.name == 'search_code_snippets'
        assert explore_structure.name == 'explore_tree_structure'
    
    def test_all_tools_implement_required_methods(self):
        """Test that all LocAgent tools implement required methods."""
        from openhands.agenthub.loc_agent.tools.unified import (
            ExploreStructureTool,
            SearchEntityTool,
            SearchRepoTool,
        )
        
        tools = [
            SearchEntityTool(),
            SearchRepoTool(),
            ExploreStructureTool(),
        ]
        
        for tool in tools:
            # Should have get_schema method
            schema = tool.get_schema()
            assert 'type' in schema
            assert 'function' in schema
            
            # Should have validate_parameters method
            assert hasattr(tool, 'validate_parameters')
            assert callable(tool.validate_parameters)