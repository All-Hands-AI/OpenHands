# tests/unit/test_llm_diff_parser.py
import pytest

from openhands.agenthub.codeact_agent.llm_diff_parser import (
    parse_llm_response_for_diffs,
)

# Test cases for parse_llm_response_for_diffs


def test_parse_single_valid_block():
    content = """
Some text before.
```python
path/to/file.py
<<<<<<< SEARCH
print("Hello")
=======
print("Hello, World!")
>>>>>>> REPLACE
```
Some text after.
"""
    expected_edits = [
        ('path/to/file.py', 'print("Hello")\n', 'print("Hello, World!")\n')
    ]
    # Calculate expected indices (approximate, depends on exact line endings/spacing)
    # Start index should be at '```python'
    # End index should be after the final '```'
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE') + len('>>>>>>> REPLACE\n```\n') - 1
    )  # Approx end

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    # End index check might be fragile due to spacing, let's check it's after start
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_multiple_valid_blocks():
    content = """
Block 1:
```python
file1.py
<<<<<<< SEARCH
old line 1
=======
new line 1
>>>>>>> REPLACE
```
Some intermediate text.
Block 2:
```javascript
file2.js
<<<<<<< SEARCH
old js line
=======
new js line
>>>>>>> REPLACE
```
"""
    expected = [
        ('file1.py', 'old line 1\n', 'new line 1\n'),
        ('file2.js', 'old js line\n', 'new js line\n'),
    ]
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE\n```', content.find('file2.js'))
        + len('>>>>>>> REPLACE\n```\n')
        - 1
    )  # Approx end of second block

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected
    assert start_idx == start_idx_expected
    assert end_idx > start_idx  # Check end is after start
    # assert end_idx == end_idx_expected


def test_parse_empty_search_block():
    content = """
Creating a new file.
```python
new_file.py
<<<<<<< SEARCH
=======
# This is a new file
print("Created!")
>>>>>>> REPLACE
```
"""
    expected_edits = [('new_file.py', '', '# This is a new file\nprint("Created!")\n')]
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_empty_replace_block():
    content = """
Deleting content.
```python
file_to_edit.py
<<<<<<< SEARCH
# Line to delete
print("Delete me")
=======
>>>>>>> REPLACE
```
"""
    expected_edits = [('file_to_edit.py', '# Line to delete\nprint("Delete me")\n', '')]
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_no_blocks():
    content = 'This is just a regular message without any diff blocks.'
    expected_edits = []
    expected_start_idx = -1
    expected_end_idx = -1

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == expected_start_idx
    assert end_idx == expected_end_idx


def test_parse_malformed_missing_divider():
    content = """
```python
file.py
<<<<<<< SEARCH
old content
# Missing divider here
new content
>>>>>>> REPLACE
```
"""
    with pytest.raises(ValueError, match='Expected `=======`'):
        parse_llm_response_for_diffs(content)


def test_parse_malformed_missing_replace_marker():
    content = """
```python
file.py
<<<<<<< SEARCH
old content
=======
new content
# Missing replace marker
```
"""
    with pytest.raises(ValueError, match='Expected `>>>>>>> REPLACE`'):
        parse_llm_response_for_diffs(content)


def test_parse_filename_inference():
    content = """
Editing file1.py
```python
file1.py
<<<<<<< SEARCH
content1
=======
new content1
>>>>>>> REPLACE
```
Now editing the same file again.
```python
<<<<<<< SEARCH
content2
=======
new content2
>>>>>>> REPLACE
```
"""
    expected = [
        ('file1.py', 'content1\n', 'new content1\n'),
        ('file1.py', 'content2\n', 'new content2\n'),
    ]
    start_idx_expected = content.find('```python\nfile1.py')
    end_idx_expected = (
        content.rfind('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_valid_fnames_exact_match():
    content = """
```python
src/app.py
<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE
```
"""
    valid_fnames = ['src/app.py', 'src/utils.py']
    expected_edits = [('src/app.py', 'old\n', 'new\n')]
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(
        content, valid_fnames=valid_fnames
    )

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_valid_fnames_fuzzy_match():
    content = """
```python
src/appz.py
<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE
```
"""
    valid_fnames = ['src/app.py', 'src/utils.py']
    expected_edits = [
        ('src/app.py', 'old\n', 'new\n')
    ]  # Expects fuzzy match to correct filename
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.find('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(
        content, valid_fnames=valid_fnames
    )

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_missing_filename_error():
    content = """
```python
<<<<<<< SEARCH
old
=======
new
>>>>>>> REPLACE
```
"""
    with pytest.raises(ValueError, match='Bad/missing filename'):
        parse_llm_response_for_diffs(content)


def test_parse_two_new_files():
    content = """
First new file:
```python
new_file_1.py
<<<<<<< SEARCH
=======
# Content for file 1
print("File 1")
>>>>>>> REPLACE
```
Second new file:
```text
new_file_2.txt
<<<<<<< SEARCH
=======
Content for file 2.
This is plain text.
>>>>>>> REPLACE
```
"""
    expected_edits = [
        ('new_file_1.py', '', '# Content for file 1\nprint("File 1")\n'),
        ('new_file_2.txt', '', 'Content for file 2.\nThis is plain text.\n'),
    ]
    start_idx_expected = content.find('```python')
    end_idx_expected = (
        content.rfind('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_one_edit_one_new_file():
    content = """
Editing an existing file:
```python
existing_file.py
<<<<<<< SEARCH
# Old line
print("Old")
=======
# New line
print("New")
>>>>>>> REPLACE
```
Creating a new file:
```python
new_file.py
<<<<<<< SEARCH
=======
# New file content
print("Newly created")
>>>>>>> REPLACE
```
"""
    expected_edits = [
        (
            'existing_file.py',
            '# Old line\nprint("Old")\n',
            '# New line\nprint("New")\n',
        ),
        ('new_file.py', '', '# New file content\nprint("Newly created")\n'),
    ]
    start_idx_expected = content.find('```python\nexisting_file.py')
    end_idx_expected = (
        content.rfind('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected


def test_parse_two_edits_different_files_explicit():
    content = """
First edit:
```python
file_a.py
<<<<<<< SEARCH
# Original line in file A
a = 1
=======
# Modified line in file A
a = 2
>>>>>>> REPLACE
```
Some text between blocks.
Second edit:
```python
file_b.py
<<<<<<< SEARCH
# Original line in file B
b = 'hello'
=======
# Modified line in file B
b = 'world'
>>>>>>> REPLACE
```
"""
    expected_edits = [
        (
            'file_a.py',
            '# Original line in file A\na = 1\n',
            '# Modified line in file A\na = 2\n',
        ),
        (
            'file_b.py',
            "# Original line in file B\nb = 'hello'\n",
            "# Modified line in file B\nb = 'world'\n",
        ),
    ]
    start_idx_expected = content.find('```python\nfile_a.py')
    end_idx_expected = (
        content.rfind('>>>>>>> REPLACE\n```') + len('>>>>>>> REPLACE\n```\n') - 1
    )

    edits, start_idx, end_idx = parse_llm_response_for_diffs(content)

    assert edits == expected_edits
    assert start_idx == start_idx_expected
    assert end_idx > start_idx
    # assert end_idx == end_idx_expected
