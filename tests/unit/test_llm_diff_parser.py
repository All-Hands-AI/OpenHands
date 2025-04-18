# tests/unit/test_llm_diff_parser.py
import pytest

from openhands.agenthub.codeact_agent.llm_diff_parser import (
    DiffBlock,
    LLMMalformedActionError,
    find_filename,  # Import if you add tests for this
    parse_llm_response_for_diffs,
    strip_filename,  # Import if you add tests for this
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
    expected_blocks = [
        DiffBlock(
            filename='path/to/file.py',
            search='print("Hello")\n',
            replace='print("Hello, World!")\n',
        )
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(filename='file1.py', search='old line 1\n', replace='new line 1\n'),
        DiffBlock(filename='file2.js', search='old js line\n', replace='new js line\n'),
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(
            filename='new_file.py',
            search='',
            replace='# This is a new file\nprint("Created!")\n',
        )
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(
            filename='file_to_edit.py',
            search='# Line to delete\nprint("Delete me")\n',
            replace='',
        )
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


def test_parse_no_blocks():
    content = 'This is just a regular message without any diff blocks.'
    expected_blocks = []

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    # The implementation raises LLMMalformedActionError for parsing issues
    with pytest.raises(LLMMalformedActionError, match='Expected `=======`'):
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
    # The implementation raises LLMMalformedActionError for parsing issues
    with pytest.raises(LLMMalformedActionError, match='Expected `>>>>>>> REPLACE`'):
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
    expected_blocks = [
        DiffBlock(filename='file1.py', search='content1\n', replace='new content1\n'),
        DiffBlock(filename='file1.py', search='content2\n', replace='new content2\n'),
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [DiffBlock(filename='src/app.py', search='old\n', replace='new\n')]

    blocks = parse_llm_response_for_diffs(content, valid_fnames=valid_fnames)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(filename='src/app.py', search='old\n', replace='new\n')
    ]  # Expects fuzzy match to correct filename

    blocks = parse_llm_response_for_diffs(content, valid_fnames=valid_fnames)

    assert blocks == expected_blocks


def test_parse_missing_filename_error_if_search_not_empty():
    # If search is not empty, a filename MUST be present or inferrable
    content = """
```python
<<<<<<< SEARCH
old content requires a filename
=======
new
>>>>>>> REPLACE
```
"""
    with pytest.raises(LLMMalformedActionError, match='Bad/missing filename'):
        parse_llm_response_for_diffs(content)


def test_parse_missing_filename_ok_if_search_empty_but_no_filename_line():
    # If search is empty (new file), but no filename line is found *at all* before the block, it's an error
    content = """
```python
<<<<<<< SEARCH
=======
new file content
>>>>>>> REPLACE
```
"""
    with pytest.raises(LLMMalformedActionError, match='Could not determine filename for new file block'):
        parse_llm_response_for_diffs(content)


def test_parse_missing_filename_ok_if_search_empty_and_filename_line_present():
    # If search is empty (new file), and a filename line *is* present, it should work
    content = """
new_file.py
```python
<<<<<<< SEARCH
=======
new file content
>>>>>>> REPLACE
```
"""
    expected_blocks = [
        DiffBlock(filename='new_file.py', search='', replace='new file content\n')
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(
            filename='new_file_1.py',
            search='',
            replace='# Content for file 1\nprint("File 1")\n',
        ),
        DiffBlock(
            filename='new_file_2.txt',
            search='',
            replace='Content for file 2.\nThis is plain text.\n',
        ),
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(
            filename='existing_file.py',
            search='# Old line\nprint("Old")\n',
            replace='# New line\nprint("New")\n',
        ),
        DiffBlock(
            filename='new_file.py',
            search='',
            replace='# New file content\nprint("Newly created")\n',
        ),
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


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
    expected_blocks = [
        DiffBlock(
            filename='file_a.py',
            search='# Original line in file A\na = 1\n',
            replace='# Modified line in file A\na = 2\n',
        ),
        DiffBlock(
            filename='file_b.py',
            search="# Original line in file B\nb = 'hello'\n",
            replace="# Modified line in file B\nb = 'world'\n",
        ),
    ]

    blocks = parse_llm_response_for_diffs(content)

    assert blocks == expected_blocks


def test_parse_block_without_closing_fence():
    content = """
```python
path/to/file.py
<<<<<<< SEARCH
print("Hello")
=======
print("Hello, World!")
>>>>>>> REPLACE
Some text after, no closing fence."""
    expected_blocks = [
        DiffBlock(
            filename='path/to/file.py',
            search='print("Hello")\n',
            replace='print("Hello, World!")\n',
        )
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks


def test_parse_block_with_extra_content_after_replace():
    # Content after REPLACE but before closing fence should be ignored by parser
    content = """
```python
path/to/file.py
<<<<<<< SEARCH
print("Hello")
=======
print("Hello, World!")
>>>>>>> REPLACE
This should be ignored.
```
More text."""
    expected_blocks = [
        DiffBlock(
            filename='path/to/file.py',
            search='print("Hello")\n',
            replace='print("Hello, World!")\n',
        )
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks


def test_parse_malformed_unexpected_divider():
    content = """
```python
file.py
<<<<<<< SEARCH
old content
=======
new content
========= UNEXPECTED DIVIDER
>>>>>>> REPLACE
```
"""
    with pytest.raises(LLMMalformedActionError, match='Unexpected `=======`'):
        parse_llm_response_for_diffs(content)


def test_find_filename_simple():
    lines = ['file.py', '```python']
    assert find_filename(lines) == 'file.py'


def test_find_filename_with_path():
    lines = ['src/core/file.py', '```python']
    assert find_filename(lines) == 'src/core/file.py'


def test_find_filename_strip_chars():
    lines = ['*`src/app.py`*', '```python']
    assert find_filename(lines) == 'src/app.py'


def test_find_filename_strip_colon():
    lines = ['File: src/app.py:', '```python']
    assert find_filename(lines) == 'src/app.py' # Assuming strip_filename handles 'File: ' prefix


def test_find_filename_no_filename():
    lines = ['Just some text', '```python']
    assert find_filename(lines) is None


def test_find_filename_too_far():
    lines = ['file.py', 'another line', 'yet another', '```python'] # file.py is too far back
    assert find_filename(lines) is None


def test_find_filename_valid_fnames_exact():
    lines = ['app.py', '```python']
    valid = ['src/app.py', 'app.py']
    assert find_filename(lines, valid_fnames=valid) == 'app.py'


def test_find_filename_valid_fnames_fuzzy():
    lines = ['appz.py', '```python']
    valid = ['src/app.py', 'app.py']
    assert find_filename(lines, valid_fnames=valid) == 'app.py'


def test_find_filename_valid_fnames_no_match():
    lines = ['other.py', '```python']
    valid = ['src/app.py', 'app.py']
    # Should still return the best guess if no valid match
    assert find_filename(lines, valid_fnames=valid) == 'other.py'


def test_strip_filename_basic():
    assert strip_filename(" file.py ") == "file.py"
    assert strip_filename("`file.py`") == "file.py"
    assert strip_filename("*file.py*") == "file.py"
    assert strip_filename("file.py:") == "file.py"
    assert strip_filename("# file.py") == "file.py"
    assert strip_filename("`*# file.py:*` ") == "file.py"


def test_strip_filename_no_strip():
    assert strip_filename("file.py") == "file.py"


def test_strip_filename_none():
    assert strip_filename(" ") is None
    assert strip_filename("```") is None
    assert strip_filename("...") is None


def test_parse_with_different_fence():
    content = """
~~~markdown
path/to/file.md
<<<<<<< SEARCH
Old text
=======
New text
>>>>>>> REPLACE
~~~
"""
    expected_blocks = [
        DiffBlock(filename='path/to/file.md', search='Old text\n', replace='New text\n')
    ]
    blocks = parse_llm_response_for_diffs(content, fence=('~~~', '~~~'))
    assert blocks == expected_blocks


def test_parse_whitespace_handling():
    # Tests if leading/trailing whitespace inside blocks is preserved
    content = """
```python
file_with_whitespace.py
<<<<<<< SEARCH
    leading whitespace
trailing whitespace    
=======
    new leading whitespace
new trailing whitespace    
>>>>>>> REPLACE
```
"""
    expected_blocks = [
        DiffBlock(
            filename='file_with_whitespace.py',
            search='    leading whitespace\ntrailing whitespace    \n',
            replace='    new leading whitespace\nnew trailing whitespace    \n',
        )
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks


def test_parse_consecutive_blocks():
    # Tests parsing blocks immediately following each other
    content = """
```python
file_a.py
<<<<<<< SEARCH
block 1 search
=======
block 1 replace
>>>>>>> REPLACE
```
```python
file_b.py
<<<<<<< SEARCH
block 2 search
=======
block 2 replace
>>>>>>> REPLACE
```
"""
    expected_blocks = [
        DiffBlock(filename='file_a.py', search='block 1 search\n', replace='block 1 replace\n'),
        DiffBlock(filename='file_b.py', search='block 2 search\n', replace='block 2 replace\n'),
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks


def test_parse_filename_like_text_in_search():
    # Tests that text resembling a filename inside SEARCH doesn't confuse the parser
    content = """
```python
real_file.py
<<<<<<< SEARCH
This line contains fake_file.py
=======
This is the replacement.
>>>>>>> REPLACE
```
"""
    expected_blocks = [
        DiffBlock(
            filename='real_file.py',
            search='This line contains fake_file.py\n',
            replace='This is the replacement.\n',
        )
    ]
    blocks = parse_llm_response_for_diffs(content)
    assert blocks == expected_blocks
