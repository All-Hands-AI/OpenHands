"""Test the EventStreamRuntime, which connects to the ActionExecutor running in the sandbox."""

import pytest
from conftest import (
    TEST_IN_CI,
    _close_test_runtime,
    _load_runtime,
)

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import (
    CmdRunAction,
    FileEditAction,
    FileReadAction,
    FileWriteAction,
    IPythonRunCellAction,
)
from openhands.events.event import FileEditSource
from openhands.events.observation import (
    CmdOutputObservation,
    ErrorObservation,
    FileReadObservation,
    FileWriteObservation,
    IPythonRunCellObservation,
)

# ============================================================================================================================
# ipython-specific tests
# ============================================================================================================================


def test_simple_cmd_ipython_and_fileop(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Test run command
    action_cmd = CmdRunAction(command='ls -l')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert 'total 0' in obs.content

    # Test run ipython
    test_code = "print('Hello, `World`!\\n')"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)

    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.content.strip() == (
        'Hello, `World`!\n'
        '[Jupyter current working directory: /openhands/workspace]\n'
        '[Jupyter Python interpreter: /openhands/poetry/openhands-ai-5O4_aCHf-py3.12/bin/python]'
    )

    # Test read file (file should not exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_read)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, ErrorObservation)
    assert 'File not found' in obs.content

    # Test write file
    action_write = FileWriteAction(content='echo "Hello, World!"', path='hello.sh')
    logger.info(action_write, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_write)
    assert isinstance(obs, FileWriteObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert obs.content == ''
    # event stream runtime will always use absolute path
    assert obs.path == '/openhands/workspace/hello.sh'

    # Test read file (file should exist)
    action_read = FileReadAction(path='hello.sh')
    logger.info(action_read, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_read)
    assert isinstance(
        obs, FileReadObservation
    ), 'The observation should be a FileReadObservation.'
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert obs.content == 'echo "Hello, World!"\n'
    assert obs.path == '/openhands/workspace/hello.sh'

    # clean up
    action = CmdRunAction(command='rm -rf hello.sh')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)


@pytest.mark.skipif(
    TEST_IN_CI != 'True',
    reason='This test is not working in WSL (file ownership)',
)
def test_ipython_multi_user(temp_dir, runtime_cls, run_as_openhands):
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # Test run ipython
    # get username
    test_code = "import os; print(os.environ['USER'])"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)

    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    if run_as_openhands:
        assert 'openhands' in obs.content
    else:
        assert 'root' in obs.content

    # print the current working directory
    test_code = 'import os; print(os.getcwd())'
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.content.strip()
        == (
            '/workspace\n'
            '[Jupyter current working directory: /workspace]\n'
            '[Jupyter Python interpreter: /openhands/poetry/openhands-ai-5O4_aCHf-py3.12/bin/python]'
        ).strip()
    )

    # write a file
    test_code = "with open('test.txt', 'w') as f: f.write('Hello, world!')"
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_ipython)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, IPythonRunCellObservation)
    assert (
        obs.content.strip()
        == (
            '[Code executed successfully with no output]\n'
            '[Jupyter current working directory: /workspace]\n'
            '[Jupyter Python interpreter: /openhands/poetry/openhands-ai-5O4_aCHf-py3.12/bin/python]'
        ).strip()
    )

    # check file owner via bash
    action = CmdRunAction(command='ls -alh test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0
    if run_as_openhands:
        # -rw-r--r-- 1 openhands root 13 Jul 28 03:53 test.txt
        assert 'openhands' in obs.content.split('\r\n')[0]
    else:
        # -rw-r--r-- 1 root root 13 Jul 28 03:53 test.txt
        assert 'root' in obs.content.split('\r\n')[0]

    # clean up
    action = CmdRunAction(command='rm -rf test')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)


def test_ipython_simple(temp_dir, runtime_cls):
    runtime = _load_runtime(temp_dir, runtime_cls)

    # Test run ipython
    # get username
    test_code = 'print(1)'
    action_ipython = IPythonRunCellAction(code=test_code)
    logger.info(action_ipython, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_ipython)
    assert isinstance(obs, IPythonRunCellObservation)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        obs.content.strip()
        == (
            '1\n'
            '[Jupyter current working directory: /openhands/workspace]\n'
            '[Jupyter Python interpreter: /openhands/poetry/openhands-ai-5O4_aCHf-py3.12/bin/python]'
        ).strip()
    )

    _close_test_runtime(runtime)


def test_ipython_package_install(temp_dir, runtime_cls, run_as_openhands):
    """Make sure that cd in bash also update the current working directory in ipython."""
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands)

    # It should error out since pymsgbox is not installed
    action = IPythonRunCellAction(code='import pymsgbox')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert "ModuleNotFoundError: No module named 'pymsgbox'" in obs.content

    # Install pymsgbox in Jupyter
    action = IPythonRunCellAction(code='%pip install pymsgbox==1.0.9')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert (
        'Successfully installed pymsgbox-1.0.9' in obs.content
        or '[Package installed successfully]' in obs.content
    )

    action = IPythonRunCellAction(code='import pymsgbox')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    # import should not error out
    assert obs.content.strip() == (
        '[Code executed successfully with no output]\n'
        '[Jupyter current working directory: /openhands/workspace]\n'
        '[Jupyter Python interpreter: /openhands/poetry/openhands-ai-5O4_aCHf-py3.12/bin/python]'
    )

    _close_test_runtime(runtime)


def test_ipython_file_editor_permissions_as_openhands(temp_dir, runtime_cls):
    """Test file editor permission behavior when running as different users."""
    runtime = _load_runtime(temp_dir, runtime_cls, run_as_openhands=True)

    # Create a file owned by root with restricted permissions
    action = CmdRunAction(
        command='sudo touch /root/test.txt && sudo chmod 600 /root/test.txt'
    )
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    # Try to view the file as openhands user - should fail with permission denied
    test_code = "print(file_editor(command='view', path='/root/test.txt'))"
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to edit the file as openhands user - should fail with permission denied
    test_code = "print(file_editor(command='str_replace', path='/root/test.txt', old_str='', new_str='test'))"
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to create a file in root directory - should fail with permission denied
    test_code = (
        "print(file_editor(command='create', path='/root/new.txt', file_text='test'))"
    )
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'Permission denied' in obs.content

    # Try to use file editor in openhands sandbox directory - should work
    test_code = """
# Create file
print(file_editor(command='create', path='/openhands/workspace/test.txt', file_text='Line 1\\nLine 2\\nLine 3'))

# View file
print(file_editor(command='view', path='/openhands/workspace/test.txt'))

# Edit file
print(file_editor(command='str_replace', path='/openhands/workspace/test.txt', old_str='Line 2', new_str='New Line 2'))

# Undo edit
print(file_editor(command='undo_edit', path='/openhands/workspace/test.txt'))
"""
    action = IPythonRunCellAction(code=test_code)
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert 'File created successfully' in obs.content
    assert 'Line 1' in obs.content
    assert 'Line 2' in obs.content
    assert 'Line 3' in obs.content
    assert 'New Line 2' in obs.content
    assert 'Last edit to' in obs.content
    assert 'undone successfully' in obs.content

    # Clean up
    action = CmdRunAction(command='rm -f /openhands/workspace/test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    action = CmdRunAction(command='sudo rm -f /root/test.txt')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)


def test_file_read_and_edit_via_oh_aci(runtime_cls, run_as_openhands):
    runtime = _load_runtime(None, runtime_cls, run_as_openhands)
    sandbox_dir = '/openhands/workspace'

    actions = [
        {
            'command': 'create',
            'test_code': f"print(file_editor(command='create', path='{sandbox_dir}/test.txt', file_text='Line 1\\nLine 2\\nLine 3'))",
            'action_cls': FileEditAction,
            'assertions': ['File created successfully'],
        },
        {
            'command': 'view',
            'test_code': f"print(file_editor(command='view', path='{sandbox_dir}/test.txt'))",
            'action_cls': FileReadAction,
            'assertions': ['Line 1', 'Line 2', 'Line 3'],
        },
        {
            'command': 'str_replace',
            'test_code': f"print(file_editor(command='str_replace', path='{sandbox_dir}/test.txt', old_str='Line 2', new_str='New Line 2'))",
            'action_cls': FileEditAction,
            'assertions': ['New Line 2'],
        },
        {
            'command': 'undo_edit',
            'test_code': f"print(file_editor(command='undo_edit', path='{sandbox_dir}/test.txt'))",
            'action_cls': FileEditAction,
            'assertions': ['Last edit to', 'undone successfully'],
        },
        {
            'command': 'insert',
            'test_code': f"print(file_editor(command='insert', path='{sandbox_dir}/test.txt', insert_line=2, new_str='Line 4'))",
            'action_cls': FileEditAction,
            'assertions': ['Line 4'],
        },
    ]

    for action_info in actions:
        action_cls = action_info['action_cls']

        kwargs = {
            'path': f'{sandbox_dir}/test.txt',
            'translated_ipython_code': action_info['test_code'],
            'impl_source': FileEditSource.OH_ACI,
        }
        if action_info['action_cls'] == FileEditAction:
            kwargs['content'] = ''  # dummy value required for FileEditAction

        action = action_cls(**kwargs)

        logger.info(action, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        for assertion in action_info['assertions']:
            if action_cls == FileReadAction:
                assert assertion in obs.content
            else:
                assert assertion in str(obs)

    _close_test_runtime(runtime)
