"""Tests for tool inheritance patterns between agents."""

import pytest

from openhands.agenthub.codeact_agent.tools.unified import (
    FinishTool, BashTool, FileEditorTool, BrowserTool
)
from openhands.agenthub.readonly_agent.tools.unified import (
    ViewTool, GrepTool, GlobTool
)


class TestCodeActToolsAvailability:
    """Test that CodeAct tools are properly available."""
    
    def test_codeact_tools_instantiation(self):
        """Test that all CodeAct tools can be instantiated."""
        finish_tool = FinishTool()
        bash_tool = BashTool()
        file_tool = FileEditorTool()
        browser_tool = BrowserTool()
        
        assert finish_tool.name == 'finish'
        assert bash_tool.name == 'execute_bash'
        assert file_tool.name == 'str_replace_editor'
        assert browser_tool.name == 'browser'
    
    def test_codeact_tools_schemas(self):
        """Test that CodeAct tools generate valid schemas."""
        tools = [FinishTool(), BashTool(), FileEditorTool(), BrowserTool()]
        
        for tool in tools:
            schema = tool.get_schema()
            assert schema['type'] == 'function'
            assert 'function' in schema
            assert 'name' in schema['function']
            assert 'description' in schema['function']
            assert 'parameters' in schema['function']


class TestReadOnlyToolsAvailability:
    """Test that ReadOnly tools are properly available."""
    
    def test_readonly_tools_instantiation(self):
        """Test that all ReadOnly tools can be instantiated."""
        view_tool = ViewTool()
        grep_tool = GrepTool()
        glob_tool = GlobTool()
        
        assert view_tool.name == 'view'
        assert grep_tool.name == 'grep'
        assert glob_tool.name == 'glob'
    
    def test_readonly_tools_schemas(self):
        """Test that ReadOnly tools generate valid schemas."""
        tools = [ViewTool(), GrepTool(), GlobTool()]
        
        for tool in tools:
            schema = tool.get_schema()
            assert schema['type'] == 'function'
            assert 'function' in schema
            assert 'name' in schema['function']
            assert 'description' in schema['function']
            assert 'parameters' in schema['function']


class TestInheritancePattern:
    """Test the inheritance pattern between CodeAct and ReadOnly agents."""
    
    def test_readonly_inherits_finish_tool(self):
        """Test that ReadOnly can import and use FinishTool from CodeAct."""
        # This import should work due to inheritance
        from openhands.agenthub.readonly_agent.tools.unified import FinishTool as ReadOnlyFinish
        from openhands.agenthub.codeact_agent.tools.unified import FinishTool as CodeActFinish
        
        # Should be the same class
        assert ReadOnlyFinish is CodeActFinish
        
        # Should work the same way
        readonly_finish = ReadOnlyFinish()
        codeact_finish = CodeActFinish()
        
        assert readonly_finish.name == codeact_finish.name
        assert readonly_finish.description == codeact_finish.description
    
    def test_readonly_has_own_tools(self):
        """Test that ReadOnly has its own specific tools."""
        view_tool = ViewTool()
        grep_tool = GrepTool()
        glob_tool = GlobTool()
        
        # These should be ReadOnly-specific
        assert view_tool.name == 'view'
        assert grep_tool.name == 'grep'
        assert glob_tool.name == 'glob'
        
        # Verify they have safe, read-only functionality
        view_schema = view_tool.get_schema()
        assert 'read' in view_schema['function']['description'].lower() or 'view' in view_schema['function']['description'].lower()
        
        grep_schema = grep_tool.get_schema()
        assert 'search' in grep_schema['function']['description'].lower()
    
    def test_readonly_does_not_inherit_dangerous_tools(self):
        """Test that ReadOnly doesn't have access to dangerous CodeAct tools."""
        # ReadOnly should not be able to import dangerous tools directly
        with pytest.raises(ImportError):
            from openhands.agenthub.readonly_agent.tools.unified import BashTool
        
        with pytest.raises(ImportError):
            from openhands.agenthub.readonly_agent.tools.unified import FileEditorTool
        
        with pytest.raises(ImportError):
            from openhands.agenthub.readonly_agent.tools.unified import BrowserTool


class TestToolSafety:
    """Test that tools have appropriate safety characteristics."""
    
    def test_codeact_tools_are_powerful(self):
        """Test that CodeAct tools have powerful capabilities."""
        bash_tool = BashTool()
        file_tool = FileEditorTool()
        
        bash_schema = bash_tool.get_schema()
        file_schema = file_tool.get_schema()
        
        # Should mention execution/modification capabilities
        bash_desc = bash_schema['function']['description'].lower()
        assert any(word in bash_desc for word in ['execute', 'command', 'bash', 'run'])
        
        file_desc = file_schema['function']['description'].lower()
        assert any(word in file_desc for word in ['edit', 'create', 'modify', 'write'])
    
    def test_readonly_tools_are_safe(self):
        """Test that ReadOnly tools are safe and read-only."""
        view_tool = ViewTool()
        grep_tool = GrepTool()
        glob_tool = GlobTool()
        
        view_desc = view_tool.get_schema()['function']['description'].lower()
        grep_desc = grep_tool.get_schema()['function']['description'].lower()
        glob_desc = glob_tool.get_schema()['function']['description'].lower()
        
        # Should not mention modification capabilities (but "read" is safe)
        dangerous_words = ['edit', 'modify', 'write', 'delete', 'execute', 'create']
        # Note: 'run' removed because it appears in 'truncated' in ViewTool description
        
        for desc in [view_desc, grep_desc, glob_desc]:
            assert not any(word in desc for word in dangerous_words), f"Found dangerous word in: {desc}"
        
        # Should mention safe operations
        safe_words = ['read', 'view', 'search', 'find', 'list', 'display']
        assert any(word in view_desc for word in safe_words)
        assert any(word in grep_desc for word in safe_words)
        assert any(word in glob_desc for word in safe_words)


class TestToolParameterValidation:
    """Test that inherited and own tools validate parameters correctly."""
    
    def test_inherited_finish_tool_validation(self):
        """Test that inherited FinishTool validates parameters correctly."""
        from openhands.agenthub.readonly_agent.tools.unified import FinishTool
        
        finish_tool = FinishTool()
        
        # Valid parameters
        valid_params = {'summary': 'Task completed successfully'}
        validated = finish_tool.validate_parameters(valid_params)
        assert 'summary' in validated
        
        # Empty parameters should work (no required params)
        validated = finish_tool.validate_parameters({})
        assert validated == {}
    
    def test_readonly_tool_validation(self):
        """Test that ReadOnly-specific tools validate parameters correctly."""
        view_tool = ViewTool()
        grep_tool = GrepTool()
        glob_tool = GlobTool()
        
        # Test ViewTool validation
        view_params = {'path': '/test/path'}
        validated = view_tool.validate_parameters(view_params)
        assert validated['path'] == '/test/path'
        
        # Test GrepTool validation
        grep_params = {'pattern': 'test', 'path': '/test'}
        validated = grep_tool.validate_parameters(grep_params)
        assert validated['pattern'] == 'test'
        assert validated['path'] == '/test'
        
        # Test GlobTool validation
        glob_params = {'pattern': '*.py'}
        validated = glob_tool.validate_parameters(glob_params)
        assert validated['pattern'] == '*.py'


class TestAgentToolSeparation:
    """Test that agent tools are properly separated and organized."""
    
    def test_codeact_tool_imports(self):
        """Test that CodeAct tools can be imported from their location."""
        from openhands.agenthub.codeact_agent.tools.unified import (
            Tool, ToolError, ToolValidationError,
            BashTool, FileEditorTool, BrowserTool, FinishTool
        )
        
        # Should be able to instantiate all
        tools = [BashTool(), FileEditorTool(), BrowserTool(), FinishTool()]
        assert len(tools) == 4
        
        # All should be Tool instances
        for tool in tools:
            assert isinstance(tool, Tool)
    
    def test_readonly_tool_imports(self):
        """Test that ReadOnly tools can be imported from their location."""
        from openhands.agenthub.readonly_agent.tools.unified import (
            FinishTool, ViewTool, GrepTool, GlobTool
        )
        
        # Should be able to instantiate all
        tools = [FinishTool(), ViewTool(), GrepTool(), GlobTool()]
        assert len(tools) == 4
        
        # All should be Tool instances
        from openhands.agenthub.codeact_agent.tools.unified.base import Tool
        for tool in tools:
            assert isinstance(tool, Tool)
    
    def test_tool_name_uniqueness_within_agent(self):
        """Test that tool names are unique within each agent."""
        # CodeAct tools
        codeact_tools = [BashTool(), FileEditorTool(), BrowserTool(), FinishTool()]
        codeact_names = [tool.name for tool in codeact_tools]
        assert len(codeact_names) == len(set(codeact_names)), "CodeAct tool names should be unique"
        
        # ReadOnly tools
        readonly_tools = [ViewTool(), GrepTool(), GlobTool()]
        readonly_names = [tool.name for tool in readonly_tools]
        assert len(readonly_names) == len(set(readonly_names)), "ReadOnly tool names should be unique"