"""Bash-related tests for the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import os
from pathlib import Path

import pytest
from conftest import (
    _close_test_runtime,
    _get_sandbox_folder,
    _load_runtime,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import CmdRunAction
from openhands.events.observation import CmdOutputObservation, ErrorObservation
from openhands.runtime.base import Runtime

# ============================================================================================================================
# Bash-specific tests
# ============================================================================================================================


def _run_cmd_action(runtime, custom_command: str):
    action = CmdRunAction(command=custom_command)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    assert isinstance(obs, (CmdOutputObservation, ErrorObservation))
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    return obs


def test_bash_command_env(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        obs = runtime.run_action(CmdRunAction(command='env'))
        assert isinstance(
            obs, CmdOutputObservation
        ), 'The observation should be a CmdOutputObservation.'
        assert obs.exit_code == 0, 'The exit code should be 0.'
    finally:
        _close_test_runtime(runtime)


def test_bash_server(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        action = CmdRunAction(command='python3 -m http.server 8080')
        action.timeout = 1
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1
        assert 'Serving HTTP on 0.0.0.0 port 8080' in obs.content
        assert (
            "[The command timed out after 1 seconds. You may wait longer to see additional output by sending empty command '', send other commands to interact with the current process, or send keys to interrupt/kill the command.]"
            in obs.metadata.suffix
        )

        action = CmdRunAction(command='C-c')
        action.timeout = 30
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'Keyboard interrupt received, exiting.' in obs.content
        assert '/workspace' in obs.metadata.working_dir

        action = CmdRunAction(command='ls')
        action.timeout = 1
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'Keyboard interrupt received, exiting.' not in obs.content
        assert '/workspace' in obs.metadata.working_dir

        # run it again!
        action = CmdRunAction(command='python3 -m http.server 8080')
        action.timeout = 1
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == -1
        assert 'Serving HTTP on 0.0.0.0 port 8080' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_multiline_commands(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        # single multiline command
        obs = _run_cmd_action(runtime, 'echo \\\n -e "foo"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'foo' in obs.content

        # test multiline echo
        obs = _run_cmd_action(runtime, 'echo -e "hello\nworld"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'hello\nworld' in obs.content

        # test whitespace
        obs = _run_cmd_action(runtime, 'echo -e "a\\n\\n\\nz"')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert '\n\n\n' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multiple_multiline_commands(temp_dir, runtime_cls, run_as_openhands):
    cmds = [
        'ls -l',
        'echo -e "hello\nworld"',
        """echo -e "hello it's me\"""",
        """echo \\
    -e 'hello' \\
    -v""",
        """echo -e 'hello\\nworld\\nare\\nyou\\nthere?'""",
        """echo -e 'hello\nworld\nare\nyou\n\nthere?'""",
        """echo -e 'hello\nworld "'""",
    ]
    joined_cmds = '\n'.join(cmds)

    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # First test that running multiple commands at once fails
        obs = _run_cmd_action(runtime, joined_cmds)
        assert isinstance(obs, ErrorObservation)
        assert 'Cannot execute multiple commands at once' in obs.content

        # Now run each command individually and verify they work
        results = []
        for cmd in cmds:
            obs = _run_cmd_action(runtime, cmd)
            assert isinstance(obs, CmdOutputObservation)
            assert obs.exit_code == 0
            results.append(obs.content)

        # Verify all expected outputs are present
        assert 'total 0' in results[0]  # ls -l
        assert 'hello\nworld' in results[1]  # echo -e "hello\nworld"
        assert "hello it's me" in results[2]  # echo -e "hello it\'s me"
        assert 'hello -v' in results[3]  # echo -e 'hello' -v
        assert (
            'hello\nworld\nare\nyou\nthere?' in results[4]
        )  # echo -e 'hello\nworld\nare\nyou\nthere?'
        assert (
            'hello\nworld\nare\nyou\n\nthere?' in results[5]
        )  # echo -e with literal newlines
        assert 'hello\nworld "' in results[6]  # echo -e with quote
    finally:
        _close_test_runtime(runtime)


def test_complex_commands(temp_dir, runtime_cls):
    cmd = """count=0; tries=0; while [ $count -lt 3 ]; do result=$(echo "Heads"); tries=$((tries+1)); echo "Flip $tries: $result"; if [ "$result" = "Heads" ]; then count=$((count+1)); else count=0; fi; done; echo "Got 3 heads in a row after $tries flips!";"""

    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        obs = _run_cmd_action(runtime, cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'Got 3 heads in a row after 3 flips!' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_no_ps2_in_output(temp_dir, runtime_cls, run_as_openhands):
    """Test that the PS2 sign is not added to the output of a multiline command."""
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, 'echo -e "hello\nworld"')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        assert 'hello\nworld' in obs.content
        assert '>' not in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multiline_command_loop(temp_dir, runtime_cls):
    # https://github.com/All-Hands-AI/OpenHands/issues/3143
    init_cmd = """mkdir -p _modules && \
for month in {01..04}; do
    for day in {01..05}; do
        touch "_modules/2024-${month}-${day}-sample.md"
    done
done && echo "created files"
"""
    follow_up_cmd = """for file in _modules/*.md; do
    new_date=$(echo $file | sed -E 's/2024-(01|02|03|04)-/2024-/;s/2024-01/2024-08/;s/2024-02/2024-09/;s/2024-03/2024-10/;s/2024-04/2024-11/')
    mv "$file" "$new_date"
done && echo "success"
"""
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        obs = _run_cmd_action(runtime, init_cmd)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'created files' in obs.content

        obs = _run_cmd_action(runtime, follow_up_cmd)
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'success' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_cmd_run(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
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


def test_run_as_user_correct_home_dir(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        obs = _run_cmd_action(runtime, 'cd ~ && pwd')
        assert obs.exit_code == 0
        if run_as_openhands:
            assert '/home/openhands' in obs.content
        else:
            assert '/root' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_multi_cmd_run_in_single_line(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        obs = _run_cmd_action(runtime, 'pwd && ls -l')
        assert obs.exit_code == 0
        assert '/workspace' in obs.content
        assert 'total 0' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_stateful_cmd(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        obs = _run_cmd_action(runtime, 'mkdir -p test')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        obs = _run_cmd_action(runtime, 'cd test')
        assert obs.exit_code == 0, 'The exit code should be 0.'

        obs = _run_cmd_action(runtime, 'pwd')
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert '/workspace/test' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_failed_cmd(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        obs = _run_cmd_action(runtime, 'non_existing_command')
        assert obs.exit_code != 0, 'The exit code should not be 0 for a failed command.'
    finally:
        _close_test_runtime(runtime)


def _create_test_file(host_temp_dir):
    # Single file
    with open(os.path.join(host_temp_dir, 'test_file.txt'), 'w') as f:
        f.write('Hello, World!')


def test_copy_single_file(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
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


def test_copy_directory_recursively(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)

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


def test_copy_to_non_existent_directory(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
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


def test_overwrite_existing_file(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
    try:
        sandbox_dir = '/openhands/workspace'

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


def test_copy_non_existent_file(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)
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


def test_copy_from_directory(temp_dir, runtime_cls):
    runtime: Runtime = _load_runtime(temp_dir, runtime_cls)
    sandbox_dir = _get_sandbox_folder(runtime)
    try:
        temp_dir_copy = os.path.join(temp_dir, 'test_dir')
        # We need a separate directory, since temp_dir is mounted to /workspace
        _create_host_test_dir_with_files(temp_dir_copy)

        # Initial state
        runtime.copy_to(temp_dir_copy, sandbox_dir, recursive=True)

        path_to_copy_from = f'{sandbox_dir}/test_dir'
        result = runtime.copy_from(path=path_to_copy_from)

        # Result is returned as a path
        assert isinstance(result, Path)

        result.unlink()
    finally:
        _close_test_runtime(runtime)


def test_git_operation(runtime_cls):
    # do not mount workspace, since workspace mount by tests will be owned by root
    # while the user_id we get via os.getuid() is different from root
    # which causes permission issues
    runtime = _load_runtime(
        temp_dir=None,
        use_workspace=False,
        runtime_cls=runtime_cls,
        # Need to use non-root user to expose issues
        run_as_openhands=True,
    )
    # this will happen if permission of runtime is not properly configured
    # fatal: detected dubious ownership in repository at '/workspace'
    try:
        obs = _run_cmd_action(runtime, 'sudo chown -R openhands:root .')
        assert obs.exit_code == 0

        # check the ownership of the current directory
        obs = _run_cmd_action(runtime, 'ls -alh .')
        assert obs.exit_code == 0
        # drwx--S--- 2 openhands root   64 Aug  7 23:32 .
        # drwxr-xr-x 1 root      root 4.0K Aug  7 23:33 ..
        for line in obs.content.split('\n'):
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
        obs = _run_cmd_action(runtime, 'git diff --no-color --cached')
        assert obs.exit_code == 0
        assert 'b/test_file.txt' in obs.content
        assert '+hello' in obs.content

        # git commit
        obs = _run_cmd_action(runtime, 'git commit -m "test commit"')
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)


def test_python_version(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        obs = runtime.run_action(CmdRunAction(command='python --version'))

        assert isinstance(
            obs, CmdOutputObservation
        ), 'The observation should be a CmdOutputObservation.'
        assert obs.exit_code == 0, 'The exit code should be 0.'
        assert 'Python 3' in obs.content, 'The output should contain "Python 3".'
    finally:
        _close_test_runtime(runtime)


def test_pwd_property(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a subdirectory and verify pwd updates
        obs = _run_cmd_action(runtime, 'mkdir -p random_dir')
        assert obs.exit_code == 0

        obs = _run_cmd_action(runtime, 'cd random_dir && pwd')
        assert obs.exit_code == 0
        assert 'random_dir' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_basic_command(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test simple command
        obs = _run_cmd_action(runtime, "echo 'hello world'")
        assert 'hello world' in obs.content
        assert obs.exit_code == 0

        # Test command with error
        obs = _run_cmd_action(runtime, 'nonexistent_command')
        assert obs.exit_code == 127
        assert 'nonexistent_command: command not found' in obs.content

        # Test command with special characters
        obs = _run_cmd_action(runtime, "echo 'hello   world    with\nspecial  chars'")
        assert 'hello   world    with\nspecial  chars' in obs.content
        assert obs.exit_code == 0

        # Test multiple commands in sequence
        obs = _run_cmd_action(runtime, 'echo "first" && echo "second" && echo "third"')
        assert 'first' in obs.content
        assert 'second' in obs.content
        assert 'third' in obs.content
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)


def test_interactive_command(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test interactive command
        action = CmdRunAction('read -p "Enter name: " name && echo "Hello $name"')
        action.timeout = 1
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        # assert 'Enter name:' in obs.content # FIXME: this is not working
        assert '[The command timed out after 1 seconds.' in obs.metadata.suffix

        action = CmdRunAction('John')
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Hello John' in obs.content
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix

        # Test multiline command input with here document
        action = CmdRunAction("""cat << EOF
line 1
line 2
EOF""")
        obs = runtime.run_action(action)
        assert 'line 1\nline 2' in obs.content
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
        assert obs.exit_code == 0
    finally:
        _close_test_runtime(runtime)


def test_long_output(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Generate a long output
        action = CmdRunAction('for i in $(seq 1 5000); do echo "Line $i"; done')
        action.timeout = 10
        obs = runtime.run_action(action)
        assert obs.exit_code == 0
        assert 'Line 1' in obs.content
        assert 'Line 5000' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_long_output_exceed_history_limit(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Generate a long output
        action = CmdRunAction('for i in $(seq 1 50000); do echo "Line $i"; done')
        action.timeout = 30
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert 'Previous command outputs are truncated' in obs.metadata.prefix
        assert 'Line 40000' in obs.content
        assert 'Line 50000' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_long_output_from_nested_directories(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create nested directories with many files
        setup_cmd = 'mkdir -p /tmp/test_dir && cd /tmp/test_dir && for i in $(seq 1 100); do mkdir -p "folder_$i"; for j in $(seq 1 100); do touch "folder_$i/file_$j.txt"; done; done'
        setup_action = CmdRunAction(setup_cmd.strip())
        setup_action.timeout = 60
        obs = runtime.run_action(setup_action)
        assert obs.exit_code == 0

        # List the directory structure recursively
        action = CmdRunAction('ls -R /tmp/test_dir')
        action.timeout = 60
        obs = runtime.run_action(action)
        assert obs.exit_code == 0

        # Verify output contains expected files
        assert 'folder_1' in obs.content
        assert 'file_1.txt' in obs.content
        assert 'folder_100' in obs.content
        assert 'file_100.txt' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_command_backslash(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create a file with the content "implemented_function"
        action = CmdRunAction(
            'mkdir -p /tmp/test_dir && echo "implemented_function" > /tmp/test_dir/file_1.txt'
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Reproduce an issue we ran into during evaluation
        # find /workspace/sympy__sympy__1.0 -type f -exec grep -l "implemented_function" {} \;
        # find: missing argument to `-exec'
        # --> This is unexpected output due to incorrect escaping of \;
        # This tests for correct escaping of \;
        action = CmdRunAction(
            'find /tmp/test_dir -type f -exec grep -l "implemented_function" {} \\;'
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        assert '/tmp/test_dir/file_1.txt' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_command_output_continuation(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Start a command that produces output slowly
        action = CmdRunAction('for i in {1..5}; do echo $i; sleep 3; done')
        action.timeout = 2.5  # Set timeout to 2.5 seconds
        obs = runtime.run_action(action)
        assert obs.content.strip() == '1'
        assert obs.metadata.prefix == ''
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

        # Continue watching output
        action = CmdRunAction('')
        action.timeout = 2.5
        obs = runtime.run_action(action)
        assert '[Command output continued from previous command]' in obs.metadata.prefix
        assert obs.content.strip() == '2'
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

        # Continue until completion
        for expected in ['3', '4', '5']:
            action = CmdRunAction('')
            action.timeout = 2.5
            obs = runtime.run_action(action)
            assert (
                '[Command output continued from previous command]'
                in obs.metadata.prefix
            )
            assert obs.content.strip() == expected
            assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix

        # Final empty command to complete
        action = CmdRunAction('')
        obs = runtime.run_action(action)
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    finally:
        _close_test_runtime(runtime)


def test_long_running_command_follow_by_execute(
    temp_dir, runtime_cls, run_as_openhands
):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test command that produces output slowly
        action = CmdRunAction('for i in {1..3}; do echo $i; sleep 3; done')
        action.timeout = 2.5
        action.blocking = False
        obs = runtime.run_action(action)
        assert '1' in obs.content  # First number should appear before timeout
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
        assert obs.metadata.prefix == ''

        # Continue watching output
        action = CmdRunAction('')
        action.timeout = 2.5
        obs = runtime.run_action(action)
        assert '2' in obs.content
        assert (
            obs.metadata.prefix == '[Command output continued from previous command]\n'
        )
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running

        # Test command that produces no output
        action = CmdRunAction('sleep 15')
        action.timeout = 2.5
        obs = runtime.run_action(action)
        assert '3' in obs.content
        assert (
            obs.metadata.prefix == '[Command output continued from previous command]\n'
        )
        assert '[The command timed out after 2.5 seconds.' in obs.metadata.suffix
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running
    finally:
        _close_test_runtime(runtime)


def test_empty_command_errors(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test empty command without previous command
        obs = runtime.run_action(CmdRunAction(''))
        assert isinstance(obs, CmdOutputObservation)
        assert 'ERROR: No previous command to continue from' in obs.content
    finally:
        _close_test_runtime(runtime)


def test_python_interactive_input(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Test Python program that asks for input - properly escaped for bash
        python_script = """name = input('Enter your name: '); age = input('Enter your age: '); print(f'Hello {name}, you are {age} years old')"""

        # Start Python with the interactive script
        obs = runtime.run_action(CmdRunAction(f'python3 -c "{python_script}"'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Enter your name:' in obs.content
        assert obs.metadata.exit_code == -1  # -1 indicates command is still running

        # Send first input (name)
        obs = runtime.run_action(CmdRunAction('Alice'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Enter your age:' in obs.content
        assert obs.metadata.exit_code == -1

        # Send second input (age)
        obs = runtime.run_action(CmdRunAction('25'))
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert 'Hello Alice, you are 25 years old' in obs.content
        assert obs.metadata.exit_code == 0
        assert '[The command completed with exit code 0.]' in obs.metadata.suffix
    finally:
        _close_test_runtime(runtime)
