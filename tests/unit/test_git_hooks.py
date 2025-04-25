import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from openhands.events import EventStream
from openhands.events.action import FileReadAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation, FileReadObservation
from openhands.runtime.base import Runtime


class TestGitHooks:
    @pytest.fixture
    def mock_runtime(self):
        # Create a mock runtime
        mock_runtime = MagicMock(spec=Runtime)
        mock_runtime.status_callback = None
        mock_runtime.read.return_value = FileReadObservation(
            content="#!/bin/bash\necho 'Test pre-commit hook'\nexit 0",
            path='.openhands/pre-commit.sh'
        )
        mock_runtime.run_action.return_value = CmdOutputObservation(
            content="", exit_code=0, command="test command"
        )
        mock_runtime.write.return_value = None
        return mock_runtime

    def test_maybe_setup_git_hooks_success(self, mock_runtime):
        # Test successful setup of git hooks
        Runtime.maybe_setup_git_hooks(mock_runtime)
        
        # Verify that the runtime tried to read the pre-commit script
        mock_runtime.read.assert_called_with(FileReadAction(path='.openhands/pre-commit.sh'))
        
        # Verify that the runtime created the git hooks directory
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.called
        
        # Verify that the runtime made the pre-commit script executable
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.called
        
        # Verify that the runtime wrote the pre-commit hook
        mock_runtime.write.assert_called_once()
        
        # Verify that the runtime made the pre-commit hook executable
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.call_count >= 3
        
        # Verify that the runtime logged success
        mock_runtime.log.assert_called_with('info', 'Git pre-commit hook installed successfully')

    def test_maybe_setup_git_hooks_no_script(self, mock_runtime):
        # Test when pre-commit script doesn't exist
        mock_runtime.read.return_value = ErrorObservation(content="File not found")
        
        Runtime.maybe_setup_git_hooks(mock_runtime)
        
        # Verify that the runtime tried to read the pre-commit script
        mock_runtime.read.assert_called_with(FileReadAction(path='.openhands/pre-commit.sh'))
        
        # Verify that no other actions were taken
        mock_runtime.run_action.assert_not_called()
        mock_runtime.write.assert_not_called()

    def test_maybe_setup_git_hooks_mkdir_failure(self, mock_runtime):
        # Test failure to create git hooks directory
        mock_runtime.run_action.return_value = CmdOutputObservation(
            content="Permission denied", exit_code=1, command="mkdir -p .git/hooks"
        )
        
        Runtime.maybe_setup_git_hooks(mock_runtime)
        
        # Verify that the runtime tried to create the git hooks directory
        assert mock_runtime.run_action.called
        
        # Verify that the runtime logged an error
        mock_runtime.log.assert_called_with('error', 'Failed to create git hooks directory: Permission denied')
        
        # Verify that no other actions were taken
        mock_runtime.write.assert_not_called()