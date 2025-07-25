#!/usr/bin/env python3
"""
Integration test to verify function_calling.py works with unified tools.
"""

import json

from openhands.agenthub.codeact_agent.function_calling import _TOOL_INSTANCES
from openhands.core.exceptions import FunctionCallValidationError


def test_bash_tool_validation():
    """Test that BashTool validation works directly"""
    print("Testing BashTool validation...")
    
    bash_tool = _TOOL_INSTANCES['execute_bash']
    
    # Test valid parameters
    result = bash_tool.validate_parameters({"command": "echo hello"})
    assert result['command'] == "echo hello"
    assert result['is_input'] == False
    print("✓ BashTool validation successful")


def test_bash_tool_validation_error():
    """Test that BashTool validation errors are properly handled"""
    print("Testing BashTool validation error handling...")
    
    bash_tool = _TOOL_INSTANCES['execute_bash']
    
    # Test missing command
    try:
        bash_tool.validate_parameters({})
        assert False, "Expected validation error"
    except Exception as e:
        assert "Missing required parameter 'command'" in str(e)
        print("✓ BashTool validation error handling successful")


def test_finish_tool_validation():
    """Test that FinishTool validation works directly"""
    print("Testing FinishTool validation...")
    
    finish_tool = _TOOL_INSTANCES['finish']
    
    # Test valid parameters
    result = finish_tool.validate_parameters({"summary": "Task completed successfully"})
    assert result['summary'] == "Task completed successfully"
    print("✓ FinishTool validation successful")


def test_file_editor_tool_validation():
    """Test that FileEditorTool validation works directly"""
    print("Testing FileEditorTool validation...")
    
    file_editor_tool = _TOOL_INSTANCES['str_replace_editor']
    
    # Test valid parameters
    result = file_editor_tool.validate_parameters({
        "command": "view",
        "path": "/test/file.py"
    })
    assert result['command'] == "view"
    assert result['path'] == "/test/file.py"
    print("✓ FileEditorTool validation successful")


def test_browser_tool_validation():
    """Test that BrowserTool validation works directly"""
    print("Testing BrowserTool validation...")
    
    browser_tool = _TOOL_INSTANCES['browser']
    
    # Test valid parameters
    result = browser_tool.validate_parameters({
        "code": "goto('http://example.com')"
    })
    assert result['code'] == "goto('http://example.com')"
    print("✓ BrowserTool validation successful")


if __name__ == "__main__":
    test_bash_tool_validation()
    test_bash_tool_validation_error()
    test_finish_tool_validation()
    test_file_editor_tool_validation()
    test_browser_tool_validation()
    print("\n🎉 All integration tests passed!")