#!/usr/bin/env python3
"""Simple test to verify Gemini actions are working."""

import tempfile
import os
from openhands.events.action.gemini_file_editor import (
    GeminiEditAction,
    GeminiReadFileAction,
    GeminiWriteFileAction,
)
from openhands.runtime.plugins.agent_skills.gemini_file_editor.gemini_file_editor import GeminiFileEditor
from openhands.events.observation import FileReadObservation, FileEditObservation, ErrorObservation


def test_gemini_actions():
    """Test Gemini file editor actions."""
    editor = GeminiFileEditor(enable_llm_editor=False)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, world!\nThis is a test file.\n")
        temp_file = f.name
    
    try:
        # Test read action
        print("Testing read action...")
        read_action = GeminiReadFileAction(absolute_path=temp_file)
        read_obs = editor.handle_read_file_action(read_action)
        print(f"Read result: {type(read_obs).__name__}")
        if isinstance(read_obs, FileReadObservation):
            print(f"Content: {repr(read_obs.content)}")
        else:
            print(f"Error: {read_obs.content}")
        
        # Test write action
        print("\nTesting write action...")
        write_action = GeminiWriteFileAction(
            file_path=temp_file,
            content="New content\nReplaced everything!\n"
        )
        write_obs = editor.handle_write_file_action(write_action)
        print(f"Write result: {type(write_obs).__name__}")
        if isinstance(write_obs, FileEditObservation):
            print("Write successful!")
        else:
            print(f"Error: {write_obs.content}")
        
        # Test edit action
        print("\nTesting edit action...")
        edit_action = GeminiEditAction(
            file_path=temp_file,
            old_string="New content",
            new_string="Modified content",
            expected_replacements=1
        )
        edit_obs = editor.handle_edit_action(edit_action)
        print(f"Edit result: {type(edit_obs).__name__}")
        if isinstance(edit_obs, FileEditObservation):
            print("Edit successful!")
        else:
            print(f"Error: {edit_obs.content}")
        
        # Test final read
        print("\nTesting final read...")
        final_read_action = GeminiReadFileAction(absolute_path=temp_file)
        final_read_obs = editor.handle_read_file_action(final_read_action)
        print(f"Final read result: {type(final_read_obs).__name__}")
        if isinstance(final_read_obs, FileReadObservation):
            print(f"Final content: {repr(final_read_obs.content)}")
        else:
            print(f"Error: {final_read_obs.content}")
            
    finally:
        # Clean up
        os.unlink(temp_file)
    
    print("\nTest completed!")


if __name__ == "__main__":
    test_gemini_actions()