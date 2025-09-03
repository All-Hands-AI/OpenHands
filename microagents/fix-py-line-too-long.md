---
name: fix-py-line-too-long
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- E501
- line too long
---

# Instructions for fixing "E501 Line too long" errors

When you encounter E501 "line too long" errors in Python code, follow these guidelines to fix them:

## For Regular Code Lines
- Break long lines into multiple lines using appropriate line continuation
- Use parentheses, brackets, or backslashes for line continuation
- Maintain proper indentation and readability

Example:
```python
# Before (too long)
result = some_very_long_function_name(parameter1, parameter2, parameter3, parameter4, parameter5)

# After (properly formatted)
result = some_very_long_function_name(
    parameter1, parameter2, parameter3,
    parameter4, parameter5
)
```

## For Single-Line Strings
- Break single-line strings into multi-line strings using string concatenation
- Use the pattern: `"ABC"` → `("A"\n"B"\n"C")`

Example:
```python
# Before (too long)
message = "This is a very long string that exceeds the line length limit and needs to be broken up"

# After (properly formatted)
message = ("This is a very long string that exceeds the line length limit "
           "and needs to be broken up")
```

## For Long Multi-Line Strings (e.g., docstrings)
- **NEVER add type ignore comments inside the docstring**
- Add `# type: ignore` AFTER the ending `"""`
- Only use this approach for docstrings and multi-line strings

Example:
```python
# Before (too long docstring)
def example_function():
    """This is a very long docstring that exceeds the line length limit and cannot be easily broken into multiple lines without affecting readability."""
    pass

# After (with type ignore)
def example_function():
    """This is a very long docstring that exceeds the line length limit and cannot be easily broken into multiple lines without affecting readability."""  # type: ignore
    pass
```

## General Guidelines
- Prioritize code readability over strict line length compliance
- Use logical break points (after commas, operators, etc.)
- Maintain consistent indentation
- For function calls with many parameters, put each parameter on its own line
- For long conditional statements, break at logical operators (and, or, etc.)

## What NOT to do
- Do not add `# type: ignore` inside docstrings or multi-line strings
- Do not break strings in the middle of words
- Do not sacrifice code readability for line length compliance
- Do not use excessive line breaks that make code hard to follow
