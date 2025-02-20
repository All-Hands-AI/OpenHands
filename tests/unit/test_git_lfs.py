import os
import subprocess
import tempfile
from unittest import mock

import pytest

from openhands.resolver.resolve_issue import resolve_issue
from openhands.resolver.utils import Platform


@pytest.mark.asyncio
async def test_git_lfs_skip_smudge():
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock environment variables
        with mock.patch.dict(os.environ, {'GIT_LFS_SKIP_SMUDGE': '1'}):
            # Mock subprocess.check_output to verify git config is called
            with mock.patch('subprocess.check_output') as mock_check_output:
                # Mock issue handler
                mock_handler = mock.MagicMock()
                mock_handler.get_clone_url.return_value = 'https://github.com/test/repo.git'
                mock_handler.get_converted_issues.return_value = [mock.MagicMock()]

                # Mock issue_handler_factory to return our mock handler
                with mock.patch('openhands.resolver.resolve_issue.issue_handler_factory', return_value=mock_handler):
                    # Call resolve_issue with test parameters
                    await resolve_issue(
                        owner='test',
                        repo='repo',
                        token='token',
                        username='username',
                        platform=Platform.GITHUB,
                        max_iterations=1,
                        output_dir=temp_dir,
                        llm_config=mock.MagicMock(),
                        runtime_container_image=None,
                        prompt_template='',
                        issue_type='issue',
                        repo_instruction=None,
                        issue_number=1,
                        comment_id=None,
                    )

                    # Verify git config was called with correct parameters
                    mock_check_output.assert_any_call(['git', 'config', '--global', 'filter.lfs.smudge', 'git-lfs smudge --skip'])
                    mock_check_output.assert_any_call(['git', 'config', '--global', 'filter.lfs.process', 'git-lfs filter-process --skip'])


@pytest.mark.asyncio
async def test_git_clone_depth():
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock environment variables
        with mock.patch.dict(os.environ, {'GIT_CLONE_DEPTH': '1'}):
            # Mock subprocess.check_output to verify git clone is called with --depth
            with mock.patch('subprocess.check_output') as mock_check_output:
                # Mock issue handler
                mock_handler = mock.MagicMock()
                mock_handler.get_clone_url.return_value = 'https://github.com/test/repo.git'
                mock_handler.get_converted_issues.return_value = [mock.MagicMock()]

                # Mock issue_handler_factory to return our mock handler
                with mock.patch('openhands.resolver.resolve_issue.issue_handler_factory', return_value=mock_handler):
                    # Call resolve_issue with test parameters
                    await resolve_issue(
                        owner='test',
                        repo='repo',
                        token='token',
                        username='username',
                        platform=Platform.GITHUB,
                        max_iterations=1,
                        output_dir=temp_dir,
                        llm_config=mock.MagicMock(),
                        runtime_container_image=None,
                        prompt_template='',
                        issue_type='issue',
                        repo_instruction=None,
                        issue_number=1,
                        comment_id=None,
                    )

                    # Verify git clone was called with --depth
                    mock_check_output.assert_any_call([
                        'git',
                        'clone',
                        '--depth',
                        '1',
                        'https://github.com/test/repo.git',
                        f'{temp_dir}/repo',
                    ])