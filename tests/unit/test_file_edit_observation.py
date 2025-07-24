"""Tests for FileEditObservation class."""

from openhands.events.event import FileEditSource
from openhands.events.observation.files import FileEditObservation


def test_file_edit_observation_basic():
    """Test basic properties of FileEditObservation."""
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='Hello\nWorld\n',
        new_content='Hello\nNew World\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='Hello\nWorld\n',  # Initial content is old_content
    )

    assert obs.path == '/test/file.txt'
    assert obs.prev_exist is True
    assert obs.old_content == 'Hello\nWorld\n'
    assert obs.new_content == 'Hello\nNew World\n'
    assert obs.impl_source == FileEditSource.LLM_BASED_EDIT
    assert obs.message == 'I edited the file /test/file.txt.'


def test_file_edit_observation_diff_cache():
    """Test that diff visualization is cached."""
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='Hello\nWorld\n',
        new_content='Hello\nNew World\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='Hello\nWorld\n',  # Initial content is old_content
    )

    # First call should compute diff
    diff1 = obs.visualize_diff()
    assert obs._diff_cache is not None

    # Second call should use cache
    diff2 = obs.visualize_diff()
    assert diff1 == diff2


def test_file_edit_observation_no_changes():
    """Test behavior when content hasn't changed."""
    content = 'Hello\nWorld\n'
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content=content,
        new_content=content,
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content=content,  # Initial content is old_content
    )

    diff = obs.visualize_diff()
    assert '(no changes detected' in diff


def test_file_edit_observation_get_edit_groups():
    """Test the get_edit_groups method."""
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='Line 1\nLine 2\nLine 3\nLine 4\n',
        new_content='Line 1\nNew Line 2\nLine 3\nNew Line 4\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='Line 1\nLine 2\nLine 3\nLine 4\n',  # Initial content is old_content
    )

    groups = obs.get_edit_groups(n_context_lines=1)
    assert len(groups) > 0

    # Check structure of edit groups
    for group in groups:
        assert 'before_edits' in group
        assert 'after_edits' in group
        assert isinstance(group['before_edits'], list)
        assert isinstance(group['after_edits'], list)

    # Verify line numbers and content
    first_group = groups[0]
    assert any('Line 2' in line for line in first_group['before_edits'])
    assert any('New Line 2' in line for line in first_group['after_edits'])


def test_file_edit_observation_new_file():
    """Test behavior when editing a new file."""
    obs = FileEditObservation(
        path='/test/new_file.txt',
        prev_exist=False,
        old_content='',
        new_content='Hello\nWorld\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='',  # Initial content is old_content (empty for new file)
    )

    assert obs.prev_exist is False
    assert obs.old_content == ''
    assert (
        str(obs)
        == '[New file /test/new_file.txt is created with the provided content.]\n'
    )

    # Test that trying to visualize diff for a new file works
    diff = obs.visualize_diff()
    assert diff is not None


def test_file_edit_observation_context_lines():
    """Test diff visualization with different context line settings."""
    obs = FileEditObservation(
        path='/test/file.txt',
        prev_exist=True,
        old_content='Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n',
        new_content='Line 1\nNew Line 2\nLine 3\nNew Line 4\nLine 5\n',
        impl_source=FileEditSource.LLM_BASED_EDIT,
        content='Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n',  # Initial content is old_content
    )

    # Test with 0 context lines
    groups_0 = obs.get_edit_groups(n_context_lines=0)
    # Test with 2 context lines
    groups_2 = obs.get_edit_groups(n_context_lines=2)

    # More context should mean more lines in the groups
    total_lines_0 = sum(
        len(g['before_edits']) + len(g['after_edits']) for g in groups_0
    )
    total_lines_2 = sum(
        len(g['before_edits']) + len(g['after_edits']) for g in groups_2
    )
    assert total_lines_2 > total_lines_0
