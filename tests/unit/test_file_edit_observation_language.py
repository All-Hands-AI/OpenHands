"""Tests for FileEditObservation language detection."""

from openhands.events.observation.files import FileEditObservation


def test_common_extensions():
    """Test language detection for common file extensions."""
    # Test various known extensions
    test_cases = [
        ('.py', 'python'),
        ('.js', 'javascript'),
        ('.ts', 'typescript'),
        ('.jsx', 'jsx'),
        ('.tsx', 'tsx'),
        ('.html', 'html'),
        ('.css', 'css'),
        ('.json', 'json'),
        ('.md', 'markdown'),
        ('.sh', 'shell'),
        ('.yml', 'yaml'),
        ('.yaml', 'yaml'),
    ]

    for ext, expected_lang in test_cases:
        obs = FileEditObservation(
            path=f'test{ext}',
            prev_exist=True,
            old_content='',
            new_content='',
            content='',
        )
        assert obs._get_language_from_extension() == expected_lang


def test_unknown_extensions():
    """Test that unknown extensions return 'plaintext'."""
    # Test various unknown extensions
    test_cases = [
        '.unknown',
        '.xyz',
        '.foo',
        '.bar123',
    ]

    for ext in test_cases:
        obs = FileEditObservation(
            path=f'test{ext}',
            prev_exist=True,
            old_content='',
            new_content='',
            content='',
        )
        assert obs._get_language_from_extension() == 'plaintext'


def test_case_insensitivity():
    """Test that language detection is case insensitive."""
    # Test common extensions with different cases
    test_cases = [
        ('.PY', '.py', 'python'),
        ('.JS', '.js', 'javascript'),
        ('.TS', '.ts', 'typescript'),
        ('.HTML', '.html', 'html'),
        ('.CSS', '.css', 'css'),
    ]

    for upper_ext, lower_ext, expected_lang in test_cases:
        obs = FileEditObservation(
            path=f'test{upper_ext}',
            prev_exist=True,
            old_content='',
            new_content='',
            content='',
        )
        assert obs._get_language_from_extension() == expected_lang
        # Verify that lowercase and uppercase extensions return the same language
        obs_lower = FileEditObservation(
            path=f'test{lower_ext}',
            prev_exist=True,
            old_content='',
            new_content='',
            content='',
        )
        assert (
            obs._get_language_from_extension()
            == obs_lower._get_language_from_extension()
        )


def test_edge_cases():
    """Test edge cases for language detection."""
    # Test empty extension (no dot)
    obs_no_ext = FileEditObservation(
        path='test', prev_exist=True, old_content='', new_content='', content=''
    )
    assert obs_no_ext._get_language_from_extension() == 'plaintext'

    # Test multiple dots - should return plaintext as only last extension is checked
    obs_multi_dot = FileEditObservation(
        path='test.file.ext',
        prev_exist=True,
        old_content='',
        new_content='',
        content='',
    )
    assert obs_multi_dot._get_language_from_extension() == 'plaintext'

    # Test very long extension
    obs_long_ext = FileEditObservation(
        path=f'test.{"x" * 50}',
        prev_exist=True,
        old_content='',
        new_content='',
        content='',
    )
    assert obs_long_ext._get_language_from_extension() == 'plaintext'
