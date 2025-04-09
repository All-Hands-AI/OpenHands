from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FENCED_DIFF_EDIT_DESCRIPTION = '''Edit a file using Aider-style fenced SEARCH/REPLACE blocks.
This method is useful for making precise changes to code blocks.

*   You MUST provide the exact block of text to find (`SEARCH`) and the exact block of text to replace it with (`REPLACE`).
*   The `SEARCH` MUST exactly match the existing file content, including all comments, docstrings, etc.
*   Only the first occurrence of the `search` found in the file will be replaced. Ensure the `search` includes enough context to be unique if necessary.
*   To insert content into a file, provide an empty `search`. The `replace` content will be appended to the end of the file.
*   To delete content, provide an empty `replace`.

If the file contains code or other data wrapped/escaped in json/xml/quotes or other containers, you need to propose edits to the literal contents of the file, including the container markup.

*SEARCH/REPLACE* blocks will *only* replace the first match occurrence.
Including multiple unique *SEARCH/REPLACE* blocks if needed.
Include enough lines in each SEARCH section to uniquely match each set of lines that need to change.

Keep *SEARCH/REPLACE* blocks concise.
Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.
Include just the changing lines, and a few surrounding lines if needed for uniqueness.
Do not include long runs of unchanging lines in *SEARCH/REPLACE* blocks.

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

The *FULL* file path must be verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc

Pay attention to which filenames the user wants you to edit, especially if they are asking you to create a new file.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

**Format:**

Provide the arguments `path`, `search`, and `replace`.

**Example 1: Replacing a function body**

To replace the body of a function in `/path/to/file.py`:

```python
# Existing file content:
def my_function(x):
    print("old implementation")
    return x * 2

def another_function():
    pass
```

Call the tool with:
`path`: "/path/to/file.py"
`search`:
```python
def my_function(x):
    print("old implementation")
    return x * 2
```
`replace`:
```python
def my_function(x):
    # New implementation using helper
    result = helper_function(x)
    print(f"New result: {result}")
    return result
```

**Example 2: Inserting a new function**

To insert a new function at the end of `/path/to/file.py`:

Call the tool with:
`path`: "/path/to/file.py"
`search`: "" (empty string)
`replace`:
```python

def new_helper_function(y):
    """This is a new function."""
    return y + 10
```

**Example 3: Deleting a block**

To delete the `another_function` from `/path/to/file.py`:

Call the tool with:
`path`: "/path/to/file.py"
`search`:
```python

def another_function():
    pass
```
`replace`: "" (empty string)

'''

FencedDiffEditTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='fenced_diff_edit',
        description=_FENCED_DIFF_EDIT_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'The absolute path to the file to be edited.',
                },
                'search': {
                    'type': 'string',
                    'description': 'The exact contiguous block of text to search for in the file. Must match exactly, including whitespace and newlines. Use an empty string to append content.',
                },
                'replace': {
                    'type': 'string',
                    'description': 'The exact block of text to replace the search with. Use an empty string to delete the search.',
                },
            },
            'required': ['path', 'search', 'replace'],
        },
    ),
)
