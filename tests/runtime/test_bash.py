"""Bash-related tests for the EventStreamRuntime, which connects to the RuntimeClient running in the sandbox."""

import os

import pytest
from conftest import (
    TEST_IN_CI,
    _close_test_runtime,
    _get_sandbox_folder,
    _load_runtime,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation

# ============================================================================================================================
# Bash-specific tests
# ============================================================================================================================


def _run_cmd_action(runtime, custom_command: str, keep_prompt=True):
    action = CmdRunAction(command=custom_command, keep_prompt=keep_prompt)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert isinstance(obs, CmdOutputObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    return obs


def test_bash_command_pexcept(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        # We set env var PS1="\u@\h:\w $"
        # and construct the PEXCEPT prompt base on it.
        # When run `env`, bad implementation of CmdRunAction will be pexcepted by this
        # and failed to pexcept the right content, causing it fail to get error code.
        obs = runtime.run_action(CmdRunAction(command='env'))

        # For example:
        # 02:16:13 - openhands:DEBUG: client.py:78 - Executing command: env
        # 02:16:13 - openhands:DEBUG: client.py:82 - Command output: PYTHONUNBUFFERED=1
        # CONDA_EXE=/openhands/miniforge3/bin/conda
        # [...]
        # LC_CTYPE=C.UTF-8
        # PS1=\u@\h:\w $
        # 02:16:13 - openhands:DEBUG: client.py:89 - Executing command for exit code: env
        # 02:16:13 - openhands:DEBUG: client.py:92 - Exit code Output:
        # CONDA_DEFAULT_ENV=base

        # As long as the exit code is 0, the test will pass.
        assert isinstance(
            obs, CmdOutputObservation
        ), 'The observation should be a CmdOutputObservation.'
        assert obs.exit_code == 0, 'The exit code should be 0.'
    finally:
        _close_test_runtime(runtime)


def test_multiline_commands(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        # single multiline command
        obs = _run_cmd_action(runtime, 'echo \\\n -e "foo"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'foo' in obs.content

        # test multiline echo
        obs = _run_cmd_action(runtime, 'echo -e "hello\nworld"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'hello\r\nworld' in obs.content

        # test whitespace
        obs = _run_cmd_action(runtime, 'echo -e "\\n\\n\\n"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert '\r\n\r\n\r\n' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multiple_multiline_commands(temp_dir, box_class, run_as_openhands):
    cmds = [
        'ls -l',
        'echo -e "hello\nworld"',
        """
echo -e "hello it\\'s me"
""".strip(),
        """
echo \\
    -e 'hello' \\
    -v
""".strip(),
        """
echo -e 'hello\\nworld\\nare\\nyou\\nthere?'
""".strip(),
        """
echo -e 'hello
world
are
you\\n
there?'
""".strip(),
        """
echo -e 'hello
world "
'
""".strip(),
    ]
    joined_cmds = '\n'.join(cmds)

    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, joined_cmds)
        assert obs.exit_code == 0, 'The exit code should be 0.'

        assert 'total 0' in obs.content
        assert 'hello\r\nworld' in obs.content
        assert "hello it\\'s me" in obs.content
        assert 'hello -v' in obs.content
        assert 'hello\r\nworld\r\nare\r\nyou\r\nthere?' in obs.content
        assert 'hello\r\nworld\r\nare\r\nyou\r\n\r\nthere?' in obs.content
        assert 'hello\r\nworld "\r\n' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_no_ps2_in_output(temp_dir, box_class, run_as_openhands):
    """Test that the PS2 sign is not added to the output of a multiline command."""
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, 'echo -e "hello\nworld"')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        assert 'hello\r\nworld' in obs.content
        assert '>' not in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multiline_command_loop(temp_dir, box_class):
    # https://github.com/All-Hands-AI/OpenHands/issues/3143
    init_cmd = """
mkdir -p _modules && \
for month in {01..04}; do
    for day in {01..05}; do
        touch "_modules/2024-${month}-${day}-sample.md"
    done
done
echo "created files"
"""
    follow_up_cmd = """
for file in _modules/*.md; do
    new_date=$(echo $file | sed -E 's/2024-(01|02|03|04)-/2024-/;s/2024-01/2024-08/;s/2024-02/2024-09/;s/2024-03/2024-10/;s/2024-04/2024-11/')
    mv "$file" "$new_date"
done
echo "success"
"""
    runtime = _load_runtime(temp_dir, box_class)
    try:
        obs = _run_cmd_action(runtime, init_cmd)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'created files' in obs.content

        obs = _run_cmd_action(runtime, follow_up_cmd)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'success' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_cmd_run(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, 'ls -l /openhands/workspace')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, 'ls -l')
        assert obs.exit_code == 0
        assert 'total 0' in obs.content

        obs = _run_cmd_action(runtime, 'mkdir test')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, 'ls -l')
        assert obs.exit_code == 0
        if run_as_openhands:
            assert 'openhands' in obs.content
        else:
            assert 'root' in obs.content
        assert 'test' in obs.content

        obs = _run_cmd_action(runtime, 'touch test/foo.txt')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, 'ls -l test')
        assert obs.exit_code == 0
        assert 'foo.txt' in obs.content

        # clean up: this is needed, since CI will not be
        # run as root, and this test may leave a file
        # owned by root
        _run_cmd_action(runtime, 'rm -rf test')
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)


def test_run_as_user_correct_home_dir(temp_dir, box_class, run_as_openhands):
    runtime = _load_runtime(temp_dir, box_class, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, 'cd ~ && pwd')
        assert obs.exit_code == 0
        if run_as_openhands:
            assert '/home/openhands' in obs.content
        else:
            assert '/root' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multi_cmd_run_in_single_line(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        obs = _run_cmd_action(runtime, 'pwd && ls -l')
        assert obs.exit_code == 0
        assert '/workspace' in obs.content
        assert 'total 0' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_stateful_cmd(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    sandbox_dir = _get_sandbox_folder(runtime)
    try:
        obs = _run_cmd_action(runtime, 'mkdir -p test')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        obs = _run_cmd_action(runtime, 'cd test')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        obs = _run_cmd_action(runtime, 'pwd')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert f'{sandbox_dir}/test' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_failed_cmd(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        obs = _run_cmd_action(runtime, 'non_existing_command')
        assert obs.exit_code != 0, 'The exit code should not be 0 for a failed command.'
    finally:
        _close_test_runtime(runtime)


def _create_test_file(host_temp_dir):
    # Single file
    with open(os.path.join(host_temp_dir, 'test_file.txt'), 'w') as f:
        f.write('Hello, World!')


def test_copy_single_file(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        sandbox_dir = _get_sandbox_folder(runtime)
        sandbox_file = os.path.join(sandbox_dir, 'test_file.txt')
        _create_test_file(temp_dir)
        runtime.copy_to(os.path.join(temp_dir, 'test_file.txt'), sandbox_dir)

        obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
        assert obs.exit_code == 0
        assert 'test_file.txt' in obs.content

        obs = _run_cmd_action(runtime, f'cat {sandbox_file}')
        assert obs.exit_code == 0
        assert 'Hello, World!' in obs.content
    finally:
        _close_test_runtime(runtime)


def _create_host_test_dir_with_files(test_dir):
    logger.debug(f'creating `{test_dir}`')
    if not os.path.isdir(test_dir):
        os.makedirs(test_dir, exist_ok=True)
    logger.debug('creating test files in `test_dir`')
    with open(os.path.join(test_dir, 'file1.txt'), 'w') as f:
        f.write('File 1 content')
    with open(os.path.join(test_dir, 'file2.txt'), 'w') as f:
        f.write('File 2 content')


def test_copy_directory_recursively(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)

    sandbox_dir = _get_sandbox_folder(runtime)
    try:
        temp_dir_copy = os.path.join(temp_dir, 'test_dir')
        # We need a separate directory, since temp_dir is mounted to /workspace
        _create_host_test_dir_with_files(temp_dir_copy)

        runtime.copy_to(temp_dir_copy, sandbox_dir, recursive=True)

        obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
        assert obs.exit_code == 0
        assert 'test_dir' in obs.content
        assert 'file1.txt' not in obs.content
        assert 'file2.txt' not in obs.content

        obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}/test_dir')
        assert obs.exit_code == 0
        assert 'file1.txt' in obs.content
        assert 'file2.txt' in obs.content

        obs = _run_cmd_action(runtime, f'cat {sandbox_dir}/test_dir/file1.txt')
        assert obs.exit_code == 0
        assert 'File 1 content' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_copy_to_non_existent_directory(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        sandbox_dir = _get_sandbox_folder(runtime)
        _create_test_file(temp_dir)
        runtime.copy_to(
            os.path.join(temp_dir, 'test_file.txt'), f'{sandbox_dir}/new_dir'
        )

        obs = _run_cmd_action(runtime, f'cat {sandbox_dir}/new_dir/test_file.txt')
        assert obs.exit_code == 0
        assert 'Hello, World!' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_overwrite_existing_file(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        sandbox_dir = _get_sandbox_folder(runtime)

        obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, f'touch {sandbox_dir}/test_file.txt')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, f'ls -alh {sandbox_dir}')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, f'cat {sandbox_dir}/test_file.txt')
        assert obs.exit_code == 0
        assert 'Hello, World!' not in obs.content

        _create_test_file(temp_dir)
        runtime.copy_to(os.path.join(temp_dir, 'test_file.txt'), sandbox_dir)

        obs = _run_cmd_action(runtime, f'cat {sandbox_dir}/test_file.txt')
        assert obs.exit_code == 0
        assert 'Hello, World!' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_copy_non_existent_file(temp_dir, box_class):
    runtime = _load_runtime(temp_dir, box_class)
    try:
        sandbox_dir = _get_sandbox_folder(runtime)
        with pytest.raises(FileNotFoundError):
            runtime.copy_to(
                os.path.join(sandbox_dir, 'non_existent_file.txt'),
                f'{sandbox_dir}/should_not_exist.txt',
            )

        obs = _run_cmd_action(runtime, f'ls {sandbox_dir}/should_not_exist.txt')
        assert obs.exit_code != 0  # File should not exist
    finally:
        _close_test_runtime(runtime)


def test_keep_prompt(box_class, temp_dir):
    runtime = _load_runtime(
        temp_dir,
        box_class=box_class,
        run_as_openhands=False,
    )
    try:
        sandbox_dir = _get_sandbox_folder(runtime)

        obs = _run_cmd_action(runtime, f'touch {sandbox_dir}/test_file.txt')
        assert obs.exit_code == 0
        assert 'root@' in obs.content

        obs = _run_cmd_action(
            runtime, f'cat {sandbox_dir}/test_file.txt', keep_prompt=False
        )
        assert obs.exit_code == 0
        assert 'root@' not in obs.content
    finally:
        _close_test_runtime(runtime)


@pytest.mark.skipif(
    TEST_IN_CI != 'True',
    reason='This test is not working in WSL (file ownership)',
)
def test_git_operation(box_class):
    # do not mount workspace, since workspace mount by tests will be owned by root
    # while the user_id we get via os.getuid() is different from root
    # which causes permission issues
    runtime = _load_runtime(
        temp_dir=None,
        box_class=box_class,
        # Need to use non-root user to expose issues
        run_as_openhands=True,
    )
    # this will happen if permission of runtime is not properly configured
    # fatal: detected dubious ownership in repository at '/workspace'
    try:
        # check the ownership of the current directory
        obs = _run_cmd_action(runtime, 'ls -alh .')
        assert obs.exit_code == 0
        # drwx--S--- 2 openhands root   64 Aug  7 23:32 .
        # drwxr-xr-x 1 root      root 4.0K Aug  7 23:33 ..
        for line in obs.content.split('\r\n'):
            if ' ..' in line:
                # parent directory should be owned by root
                assert 'root' in line
                assert 'openhands' not in line
            elif ' .' in line:
                # current directory should be owned by openhands
                # and its group should be root
                assert 'openhands' in line
                assert 'root' in line

        # make sure all git operations are allowed
        obs = _run_cmd_action(runtime, 'git init')
        assert obs.exit_code == 0

        # create a file
        obs = _run_cmd_action(runtime, 'echo "hello" > test_file.txt')
        assert obs.exit_code == 0

        # git add
        obs = _run_cmd_action(runtime, 'git add test_file.txt')
        assert obs.exit_code == 0

        # git diff
        obs = _run_cmd_action(runtime, 'git diff')
        assert obs.exit_code == 0

        # git commit
        obs = _run_cmd_action(runtime, 'git commit -m "test commit"')
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)
