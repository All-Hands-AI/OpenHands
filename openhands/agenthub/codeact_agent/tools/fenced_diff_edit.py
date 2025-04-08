from litellm import ChatCompletionToolParam, ChatCompletionToolParamFunctionChunk

_FENCED_DIFF_EDIT_DESCRIPTION = '''Edit a file using Aider-style SEARCH/REPLACE blocks.
This method is useful for making precise changes to existing code blocks.

*   The assistant MUST provide the exact block of text to find (`search_block`) and the exact block of text to replace it with (`replace_block`).
*   The `search_block` MUST exactly match a contiguous block of lines in the target file, including all whitespace, indentation, comments, etc.
*   Only the first occurrence of the `search_block` found in the file will be replaced. Ensure the `search_block` includes enough context to be unique if necessary.
*   To insert content into a file, provide an empty `search_block`. The `replace_block` content will be appended to the end of the file.
*   To delete content, provide an empty `replace_block`.

**Format:**

Provide the arguments `path`, `search_block`, and `replace_block`.

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
`search_block`:
```python
def my_function(x):
    print("old implementation")
    return x * 2
```
`replace_block`:
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
`search_block`: "" (empty string)
`replace_block`:
```python

def new_helper_function(y):
    """This is a new function."""
    return y + 10
```

**Example 3: Deleting a block**

To delete the `another_function` from `/path/to/file.py`:

Call the tool with:
`path`: "/path/to/file.py"
`search_block`:
```python

def another_function():
    pass
```
`replace_block`: "" (empty string)

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
                'search_block': {
                    'type': 'string',
                    'description': 'The exact contiguous block of text to search for in the file. Must match exactly, including whitespace and newlines. Use an empty string to append content.',
                },
                'replace_block': {
                    'type': 'string',
                    'description': 'The exact block of text to replace the search_block with. Use an empty string to delete the search_block.',
                },
            },
            'required': ['path', 'search_block', 'replace_block'],
        },
    ),
)
