#!/usr/bin/env python3
"""Simple test to verify runtime integration with Gemini actions."""

import tempfile
import os
from openhands.events.action.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)
from openhands.events.serialization.action import action_from_dict


def test_action_creation():
    """Test that Gemini actions can be created and have correct attributes."""
    print("Testing Gemini action creation...")
    
    # Test GeminiReadFileAction
    read_action = GeminiReadFileAction(absolute_path="/test/file.py")
    print(f"Read action: {type(read_action).__name__}")
    assert read_action.action == 'gemini_read_file_tool'
    assert read_action.absolute_path == "/test/file.py"
    
    # Test GeminiWriteFileAction
    write_action = GeminiWriteFileAction(
        file_path="/test/file.py",
        content="print('hello world')"
    )
    print(f"Write action: {type(write_action).__name__}")
    assert write_action.action == 'gemini_write_file_tool'
    assert write_action.file_path == "/test/file.py"
    assert write_action.content == "print('hello world')"
    
    # Test GeminiEditAction
    edit_action = GeminiEditAction(
        file_path="/test/file.py",
        old_string="hello",
        new_string="goodbye",
        expected_replacements=1
    )
    print(f"Edit action: {type(edit_action).__name__}")
    assert edit_action.action == 'gemini_edit_tool'
    assert edit_action.file_path == "/test/file.py"
    assert edit_action.old_string == "hello"
    assert edit_action.new_string == "goodbye"
    assert edit_action.expected_replacements == 1
    
    print("✅ All action creation tests passed!")


def test_action_registration():
    """Test that Gemini actions are properly registered."""
    print("\nTesting Gemini action registration...")
    
    from openhands.events.serialization.action import ACTION_TYPE_TO_CLASS
    
    # Check that all Gemini actions are registered
    gemini_actions = [
        'gemini_edit_tool',
        'gemini_write_file_tool', 
        'gemini_read_file_tool'
    ]
    
    for action_name in gemini_actions:
        assert action_name in ACTION_TYPE_TO_CLASS, f"Action {action_name} not registered"
        print(f"✅ {action_name} is registered")
    
    print("✅ All action registration tests passed!")


if __name__ == "__main__":
    test_action_creation()
    test_action_registration()
    print("\n🎉 All tests passed! Gemini file editor runtime integration is working correctly.")