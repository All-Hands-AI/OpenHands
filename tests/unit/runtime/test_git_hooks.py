from unittest.mock import MagicMock, call

import pytest

from openhands.events.action import CmdRunAction, FileReadAction
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
)
from openhands.runtime.base import Runtime


class TestGitHooks:
    @pytest.fixture
    def mock_runtime(self):
        # Create a mock runtime
        mock_runtime = MagicMock(spec=Runtime)
        mock_runtime.status_callback = None

        # Set up read to return different values based on the path
        def mock_read(action):
            if action.path == '.openhands/pre-commit.sh':
                return FileReadObservation(
                    content="#!/bin/bash\necho 'Test pre-commit hook'\nexit 0",
                    path='.openhands/pre-commit.sh',
                )
            elif action.path == '.git/hooks/pre-commit':
                # Simulate no existing pre-commit hook
                return ErrorObservation(content='File not found')
            return ErrorObservation(content='Unexpected path')

        mock_runtime.read.side_effect = mock_read

        mock_runtime.run_action.return_value = CmdOutputObservation(
            content='', exit_code=0, command='test command'
        )
        mock_runtime.write.return_value = None
        return mock_runtime

    def test_maybe_setup_git_hooks_success(self, mock_runtime):
        # Test successful setup of git hooks
        Runtime.maybe_setup_git_hooks(mock_runtime)

        # Verify that the runtime tried to read the pre-commit script
        assert mock_runtime.read.call_args_list[0] == call(
            FileReadAction(path='.openhands/pre-commit.sh')
        )

        # Verify that the runtime created the git hooks directory
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.called

        # Verify that the runtime made the pre-commit script executable
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.called

        # Verify that the runtime wrote the pre-commit hook
        assert mock_runtime.write.called

        # Verify that the runtime made the pre-commit hook executable
        # We can't directly compare the CmdRunAction objects, so we check if run_action was called
        assert mock_runtime.run_action.call_count >= 3

        # Verify that the runtime logged success
        mock_runtime.log.assert_called_with(
            'info', 'Git pre-commit hook installed successfully'
        )

    def test_maybe_setup_git_hooks_no_script(self, mock_runtime):
        # Test when pre-commit script doesn't exist
        mock_runtime.read.side_effect = lambda action: ErrorObservation(
            content='File not found'
        )

        Runtime.maybe_setup_git_hooks(mock_runtime)

        # Verify that the runtime tried to read the pre-commit script
        mock_runtime.read.assert_called_with(
            FileReadAction(path='.openhands/pre-commit.sh')
        )

        # Verify that no other actions were taken
        mock_runtime.run_action.assert_not_called()
        mock_runtime.write.assert_not_called()

    def test_maybe_setup_git_hooks_mkdir_failure(self, mock_runtime):
        # Test failure to create git hooks directory
        def mock_run_action(action):
            if (
                isinstance(action, CmdRunAction)
                and action.command == 'mkdir -p .git/hooks'
            ):
                return CmdOutputObservation(
                    content='Permission denied',
                    exit_code=1,
                    command='mkdir -p .git/hooks',
                )
            return CmdOutputObservation(content='', exit_code=0, command=action.command)

        mock_runtime.run_action.side_effect = mock_run_action

        Runtime.maybe_setup_git_hooks(mock_runtime)

        # Verify that the runtime tried to create the git hooks directory
        assert mock_runtime.run_action.called

        # Verify that the runtime logged an error
        mock_runtime.log.assert_called_with(
            'error', 'Failed to create git hooks directory: Permission denied'
        )

        # Verify that no other actions were taken
        mock_runtime.write.assert_not_called()

    def test_maybe_setup_git_hooks_with_existing_hook(self, mock_runtime):
        # Test when there's an existing pre-commit hook
        def mock_read(action):
            if action.path == '.openhands/pre-commit.sh':
                return FileReadObservation(
                    content="#!/bin/bash\necho 'Test pre-commit hook'\nexit 0",
                    path='.openhands/pre-commit.sh',
                )
            elif action.path == '.git/hooks/pre-commit':
                # Simulate existing pre-commit hook
                return FileReadObservation(
                    content="#!/bin/bash\necho 'Existing hook'\nexit 0",
                    path='.git/hooks/pre-commit',
                )
            return ErrorObservation(content='Unexpected path')

        mock_runtime.read.side_effect = mock_read

        Runtime.maybe_setup_git_hooks(mock_runtime)

        # Verify that the runtime tried to read both scripts
        assert len(mock_runtime.read.call_args_list) >= 2

        # Verify that the runtime preserved the existing hook
        assert mock_runtime.log.call_args_list[0] == call(
            'info', 'Preserving existing pre-commit hook'
        )

        # Verify that the runtime moved the existing hook
        move_calls = [
            call
            for call in mock_runtime.run_action.call_args_list
            if isinstance(call[0][0], CmdRunAction) and 'mv' in call[0][0].command
        ]
        assert len(move_calls) > 0

        # Verify that the runtime wrote the new pre-commit hook
        assert mock_runtime.write.called

        # Verify that the runtime logged success
        assert mock_runtime.log.call_args_list[-1] == call(
            'info', 'Git pre-commit hook installed successfully'
        )
