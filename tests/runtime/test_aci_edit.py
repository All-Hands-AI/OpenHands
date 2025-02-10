"""Editor-related tests for the DockerRuntime."""

import os

from conftest import _close_test_runtime, _load_runtime

from openhands.core.logger import openhands_logger as logger
from openhands.events.action import FileEditAction, FileWriteAction


def test_view_file(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        obs = runtime.run_action(action)

        # Test view command
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)

        assert f"Here's the result of running `cat -n` on {test_file}:" in obs.content
        assert '1\tThis is a test file.' in obs.content
        assert '2\tThis file is for testing purposes.' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_view_directory(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        obs = runtime.run_action(action)

        # Test view command
        action = FileEditAction(
            command='view',
            path=config.workspace_mount_path_in_sandbox,
        )
        obs = runtime.run_action(action)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert (
            obs.content
            == f"""Here's the files and directories up to 2 levels deep in {config.workspace_mount_path_in_sandbox}, excluding hidden items:
{config.workspace_mount_path_in_sandbox}/
{config.workspace_mount_path_in_sandbox}/test.txt"""
        )

    finally:
        _close_test_runtime(runtime)

# New tests start here

def test_create_file(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        new_file = os.path.join(config.workspace_mount_path_in_sandbox, 'new_file.txt')
        action = FileEditAction(
            command='create',
            path=new_file,
            file_text='New file content',
        )
        obs = runtime.run_action(action)
        assert 'File created successfully' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=new_file,
        )
        obs = runtime.run_action(action)
        assert 'New file content' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_str_replace(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.\nThis file is for testing purposes.',
            path=test_file,
        )
        runtime.run_action(action)

        # Test str_replace command
        action = FileEditAction(
            command='str_replace',
            path=test_file,
            old_str='test file',
            new_str='sample file',
        )
        obs = runtime.run_action(action)
        assert 'The file has been edited' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'This is a sample file.' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_insert(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='Line 1\nLine 2',
            path=test_file,
        )
        runtime.run_action(action)

        # Test insert command
        action = FileEditAction(
            command='insert',
            path=test_file,
            insert_line=1,
            new_str='Inserted line',
        )
        obs = runtime.run_action(action)
        assert 'The file has been edited' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'Line 1\nInserted line\nLine 2' in obs.content

    finally:
        _close_test_runtime(runtime)


def test_undo_edit(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(temp_dir, runtime_cls, run_as_openhands)
    try:
        # Create test file
        test_file = os.path.join(config.workspace_mount_path_in_sandbox, 'test.txt')
        action = FileWriteAction(
            content='This is a test file.',
            path=test_file,
        )
        runtime.run_action(action)

        # Make an edit
        action = FileEditAction(
            command='str_replace',
            path=test_file,
            old_str='test',
            new_str='sample',
        )
        runtime.run_action(action)

        # Undo the edit
        action = FileEditAction(
            command='undo_edit',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'Last edit to' in obs.content

        # Verify file content
        action = FileEditAction(
            command='view',
            path=test_file,
        )
        obs = runtime.run_action(action)
        assert 'This is a test file.' in obs.content

    finally:
        _close_test_runtime(runtime)

# Additional tests

def test_view_file(editor):
    editor, test_file = editor
    result = editor(command='view', path=str(test_file))
    assert isinstance(result, CLIResult)
    assert f"Here's the result of running `cat -n` on {test_file}:" in result.output
    assert '1\tThis is a test file.' in result.output
    assert '2\tThis file is for testing purposes.' in result.output


def test_view_directory(editor):
    editor, test_file = editor
    parent_dir = test_file.parent
    result = editor(command='view', path=str(parent_dir))
    assert (
        result.output
        == f"""Here's the files and directories up to 2 levels deep in {parent_dir}, excluding hidden items:
{parent_dir}/
{parent_dir}/test.txt"""
    )


def test_create_with_empty_string(editor):
    editor, test_file = editor
    new_file = test_file.parent / 'empty_content.txt'
    result = editor(command='create', path=str(new_file), file_text='')
    assert isinstance(result, ToolResult)
    assert new_file.exists()
    assert new_file.read_text() == ''
    assert 'File created successfully' in result.output


def test_create_with_none_file_text(editor):
    editor, test_file = editor
    new_file = test_file.parent / 'none_content.txt'
    with pytest.raises(EditorToolParameterMissingError) as exc_info:
        editor(command='create', path=str(new_file), file_text=None)
    assert 'file_text' in str(exc_info.value.message)


def test_str_replace_no_linting(editor):
    editor, test_file = editor
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='test file',
        new_str='sample file',
    )
    assert isinstance(result, CLIResult)

    # Test str_replace command
    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of {test_file}:
     1\tThis is a sample file.
     2\tThis file is for testing purposes.
Review the changes and make sure they are as expected. Edit the file again if necessary."""
    )

    # Test that the file content has been updated
    assert 'This is a sample file.' in test_file.read_text()


def test_str_replace_multi_line_no_linting(editor):
    editor, test_file = editor
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='This is a test file.\nThis file is for testing purposes.',
        new_str='This is a sample file.\nThis file is for testing purposes.',
    )
    assert isinstance(result, CLIResult)

    # Test str_replace command
    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of {test_file}:
     1\tThis is a sample file.
     2\tThis file is for testing purposes.
Review the changes and make sure they are as expected. Edit the file again if necessary."""
    )


def test_str_replace_multi_line_with_tabs_no_linting(editor_python_file_with_tabs):
    editor, test_file = editor_python_file_with_tabs
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='def test():\n\tprint("Hello, World!")',
        new_str='def test():\n\tprint("Hello, Universe!")',
    )
    assert isinstance(result, CLIResult)

    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of {test_file}:
     1\tdef test():
     2\t{'\t'.expandtabs()}print("Hello, Universe!")
Review the changes and make sure they are as expected. Edit the file again if necessary."""
    )


def test_str_replace_with_linting(editor):
    editor, test_file = editor
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='test file',
        new_str='sample file',
        enable_linting=True,
    )
    assert isinstance(result, CLIResult)

    # Test str_replace command
    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of {test_file}:
     1\tThis is a sample file.
     2\tThis file is for testing purposes.

No linting issues found in the changes.
Review the changes and make sure they are as expected. Edit the file again if necessary."""
    )

    # Test that the file content has been updated
    assert 'This is a sample file.' in test_file.read_text()


def test_str_replace_error_multiple_occurrences(editor):
    editor, test_file = editor
    with pytest.raises(ToolError) as exc_info:
        editor(
            command='str_replace', path=str(test_file), old_str='test', new_str='sample'
        )
    assert 'Multiple occurrences of old_str `test`' in str(exc_info.value.message)
    assert '[1, 2]' in str(exc_info.value.message)  # Should show both line numbers


def test_str_replace_error_multiple_multiline_occurrences(editor):
    editor, test_file = editor
    # Create a file with two identical multi-line blocks
    multi_block = """def example():
    print("Hello")
    return True"""
    content = f"{multi_block}\n\nprint('separator')\n\n{multi_block}"
    test_file.write_text(content)

    with pytest.raises(ToolError) as exc_info:
        editor(
            command='str_replace',
            path=str(test_file),
            old_str=multi_block,
            new_str='def new():\n    print("World")',
        )
    error_msg = str(exc_info.value.message)
    assert 'Multiple occurrences of old_str' in error_msg
    assert '[1, 7]' in error_msg  # Should show correct starting line numbers


def test_str_replace_nonexistent_string(editor):
    editor, test_file = editor
    with pytest.raises(ToolError) as exc_info:
        editor(
            command='str_replace',
            path=str(test_file),
            old_str='Non-existent Line',
            new_str='New Line',
        )
    assert 'No replacement was performed' in str(exc_info)
    assert f'old_str `Non-existent Line` did not appear verbatim in {test_file}' in str(
        exc_info.value.message
    )


def test_str_replace_with_empty_new_str(editor):
    editor, test_file = editor
    test_file.write_text('Line 1\nLine to remove\nLine 3')
    result = editor(
        command='str_replace',
        path=str(test_file),
        old_str='Line to remove\n',
        new_str='',
    )
    assert isinstance(result, CLIResult)
    assert test_file.read_text() == 'Line 1\nLine 3'


def test_str_replace_with_empty_old_str(editor):
    editor, test_file = editor
    test_file.write_text('Line 1\nLine 2\nLine 3')
    with pytest.raises(ToolError) as exc_info:
        editor(
            command='str_replace',
            path=str(test_file),
            old_str='',
            new_str='New string',
        )
    assert (
        str(exc_info.value.message)
        == """No replacement was performed. Multiple occurrences of old_str `` in lines [1, 2, 3]. Please ensure it is unique."""
    )


def test_str_replace_with_none_old_str(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterMissingError) as exc_info:
        editor(
            command='str_replace',
            path=str(test_file),
            old_str=None,
            new_str='new content',
        )
    assert 'old_str' in str(exc_info.value.message)


def test_insert_no_linting(editor):
    editor, test_file = editor
    result = editor(
        command='insert', path=str(test_file), insert_line=1, new_str='Inserted line'
    )
    assert isinstance(result, CLIResult)
    assert 'Inserted line' in test_file.read_text()
    print(result.output)
    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of the edited file:
     1\tThis is a test file.
     2\tInserted line
     3\tThis file is for testing purposes.
Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."""
    )


def test_insert_with_linting(editor):
    editor, test_file = editor
    result = editor(
        command='insert',
        path=str(test_file),
        insert_line=1,
        new_str='Inserted line',
        enable_linting=True,
    )
    assert isinstance(result, CLIResult)
    assert 'Inserted line' in test_file.read_text()
    print(result.output)
    assert (
        result.output
        == f"""The file {test_file} has been edited. Here's the result of running `cat -n` on a snippet of the edited file:
     1\tThis is a test file.
     2\tInserted line
     3\tThis file is for testing purposes.

No linting issues found in the changes.
Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."""
    )


def test_insert_invalid_line(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterInvalidError) as exc_info:
        editor(
            command='insert',
            path=str(test_file),
            insert_line=10,
            new_str='Invalid Insert',
        )
    assert 'Invalid `insert_line` parameter' in str(exc_info.value.message)
    assert 'It should be within the range of lines of the file' in str(
        exc_info.value.message
    )


def test_insert_with_empty_string(editor):
    editor, test_file = editor
    result = editor(
        command='insert',
        path=str(test_file),
        insert_line=1,
        new_str='',
    )
    assert isinstance(result, CLIResult)
    content = test_file.read_text().splitlines()
    assert '' in content
    assert len(content) == 3  # Original 2 lines plus empty line


def test_insert_with_none_new_str(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterMissingError) as exc_info:
        editor(
            command='insert',
            path=str(test_file),
            insert_line=1,
            new_str=None,
        )
    assert 'new_str' in str(exc_info.value.message)


def test_str_replace_new_str_and_old_str_same(editor):
    editor, test_file = editor
    with pytest.raises(EditorToolParameterInvalidError) as exc_info:
        editor(
            command='str_replace',
            path=str(test_file),
            old_str='test file',
            new_str='test file',
        )
    assert (
        'No replacement was performed. `new_str` and `old_str` must be different.'
        in str(exc_info.value.message)
    )


def test_view_directory_with_hidden_files(tmp_path):
    editor = OHEditor()

    # Create a directory with some test files
    test_dir = tmp_path / 'test_dir'
    test_dir.mkdir()
    (test_dir / 'visible.txt').write_text('content1')
    (test_dir / '.hidden1').write_text('hidden1')
    (test_dir / '.hidden2').write_text('hidden2')

    # Create a hidden subdirectory with a file
    hidden_subdir = test_dir / '.hidden_dir'
    hidden_subdir.mkdir()
    (hidden_subdir / 'file.txt').write_text('content3')

    # Create a visible subdirectory
    visible_subdir = test_dir / 'visible_dir'
    visible_subdir.mkdir()

    # View the directory
    result = editor(command='view', path=str(test_dir))

    # Verify output
    assert isinstance(result, CLIResult)
    assert str(test_dir) in result.output
    assert 'visible.txt' in result.output  # Visible file is shown
    assert 'visible_dir' in result.output  # Visible directory is shown
    assert '.hidden1' not in result.output  # Hidden files not shown
    assert '.hidden2' not in result.output
    assert '.hidden_dir' not in result.output
    assert (
        '3 hidden files/directories in this directory are excluded' in result.output
    )  # Shows count of hidden items in current dir only
    assert 'ls -la' in result.output  # Shows command to view hidden files


def test_view_symlinked_directory(tmp_path):
    editor = OHEditor()

    # Create a directory with some test files
    source_dir = tmp_path / 'source_dir'
    source_dir.mkdir()
    (source_dir / 'file1.txt').write_text('content1')
    (source_dir / 'file2.txt').write_text('content2')

    # Create a subdirectory with a file
    subdir = source_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'file3.txt').write_text('content3')

    # Create a symlink to the directory
    symlink_dir = tmp_path / 'symlink_dir'
    symlink_dir.symlink_to(source_dir)

    # View the symlinked directory
    result = editor(command='view', path=str(symlink_dir))

    # Verify that all files are listed through the symlink
    assert isinstance(result, CLIResult)
    assert str(symlink_dir) in result.output
    assert 'file1.txt' in result.output
    assert 'file2.txt' in result.output
    assert 'subdir' in result.output
    assert 'file3.txt' in result.output


def test_view_large_directory_with_truncation(editor, tmp_path):
    editor, _ = editor
    # Create a directory with many files to trigger truncation
    large_dir = tmp_path / 'large_dir'
    large_dir.mkdir()
    for i in range(1000):  # 1000 files should trigger truncation
        (large_dir / f'file_{i}.txt').write_text('content')

    result = editor(command='view', path=str(large_dir))
    assert isinstance(result, CLIResult)
    assert DIRECTORY_CONTENT_TRUNCATED_NOTICE in result.output


def test_view_directory_on_hidden_path(tmp_path):
    """Directory structure:
    .test_dir/
    ├── visible1.txt
    ├── .hidden1
    ├── visible_dir/
    │   ├── visible2.txt
    │   └── .hidden2
    └── .hidden_dir/
        ├── visible3.txt
        └── .hidden3
    """

    editor = OHEditor()

    # Create a directory with test files at depth 1
    hidden_test_dir = tmp_path / '.hidden_test_dir'
    hidden_test_dir.mkdir()
    (hidden_test_dir / 'visible1.txt').write_text('content1')
    (hidden_test_dir / '.hidden1').write_text('hidden1')

    # Create a visible subdirectory with visible and hidden files
    visible_subdir = hidden_test_dir / 'visible_dir'
    visible_subdir.mkdir()
    (visible_subdir / 'visible2.txt').write_text('content2')
    (visible_subdir / '.hidden2').write_text('hidden2')

    # Create a hidden subdirectory with visible and hidden files
    hidden_subdir = hidden_test_dir / '.hidden_dir'
    hidden_subdir.mkdir()
    (hidden_subdir / 'visible3.txt').write_text('content3')
    (hidden_subdir / '.hidden3').write_text('hidden3')

    # View the directory
    result = editor(command='view', path=str(hidden_test_dir))

    # Verify output
    assert isinstance(result, CLIResult)
    # Depth 1: Visible files/dirs shown, hidden files/dirs not shown
    assert 'visible1.txt' in result.output
    assert 'visible_dir' in result.output
    assert '.hidden1' not in result.output
    assert '.hidden_dir' not in result.output

    # Depth 2: Files in visible_dir shown
    assert 'visible2.txt' in result.output
    assert '.hidden2' not in result.output

    # Depth 2: Files in hidden_dir not shown
    assert 'visible3.txt' not in result.output
    assert '.hidden3' not in result.output

    # Hidden file count only includes depth 1
    assert (
        '2 hidden files/directories in this directory are excluded' in result.output
    )  # Only .hidden1 and .hidden_dir at depth 1


def test_view_large_file_with_truncation(editor, tmp_path):
    editor, _ = editor
    # Create a large file to trigger truncation
    large_file = tmp_path / 'large_test.txt'
    large_content = 'Line 1\n' * 16000  # 16000 lines should trigger truncation
    large_file.write_text(large_content)

    result = editor(command='view', path=str(large_file))
    assert isinstance(result, CLIResult)
    assert FILE_CONTENT_TRUNCATED_NOTICE in result.output


def test_validate_path_suggests_absolute_path(editor):
    editor, test_file = editor
    relative_path = test_file.name  # This is a relative path
    with pytest.raises(EditorToolParameterInvalidError) as exc_info:
        editor(command='view', path=relative_path)
    error_message = str(exc_info.value.message)
    assert 'The path should be an absolute path' in error_message
    assert 'Maybe you meant' in error_message
    suggested_path = error_message.split('Maybe you meant ')[1].strip('?')
    assert Path(suggested_path).is_absolute()
