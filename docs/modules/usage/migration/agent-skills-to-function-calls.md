# Migrating from Agent Skills to Function Calls

This guide helps you migrate from the legacy agent skills to the new function calling interface in OpenHands.

## Overview

OpenHands has migrated from agent skills to a unified function calling interface for better maintainability and performance. This change was introduced in version 0.21.0 and the legacy agent skills will be removed in version 0.22.0.

## Timeline

- **0.21.0**: Deprecation notice added
- **0.22.0**: Legacy agent skills will be removed

## Migration Guide

### File Operations

#### Before (Agent Skills):
```python
from openhands.runtime.plugins.agent_skills.file_ops import open_file, search_file

# Open and read a file
open_file("/path/to/file.txt")

# Search in a file
search_file("search term", "/path/to/file.txt")
```

#### After (Function Calls):
```python
# Use the str_replace_editor function
{
    "command": "view",
    "path": "/path/to/file.txt"
}

# Use execute_bash for searching
{
    "command": "grep -n 'search term' /path/to/file.txt"
}
```

### File Parsing

#### Before (Agent Skills):
```python
from openhands.runtime.plugins.agent_skills.file_reader import parse_pdf, parse_docx

# Parse PDF
parse_pdf("/path/to/document.pdf")

# Parse DOCX
parse_docx("/path/to/document.docx")
```

#### After (Function Calls):
```python
# Use execute_python_cell for parsing
{
    "code": """
import PyPDF2
with open('/path/to/document.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        print(page.extract_text())
"""
}

# Or use docx for Word documents
{
    "code": """
import docx
doc = docx.Document('/path/to/document.docx')
for para in doc.paragraphs:
    print(para.text)
"""
}
```

### Web Browsing

#### Before (Agent Skills):
```python
from openhands.runtime.plugins.agent_skills.browsing_agent import browse_url

# Browse a webpage
browse_url("https://example.com")
```

#### After (Function Calls):
```python
# Use web_read for simple content reading
{
    "url": "https://example.com"
}

# Use browser for interactive browsing
{
    "code": """
goto('https://example.com')
click('a51')  # Click element with ID 'a51'
"""
}
```

## Configuration Changes

### Before:
```toml
[agent]
enable_agent_skills = true
```

### After:
```toml
[agent]
codeact_enable_browsing = true
codeact_enable_jupyter = true
codeact_enable_llm_editor = false
```

## Benefits of Function Calling

1. **Unified Interface**: All actions are performed through a consistent function calling interface
2. **Better Type Safety**: Function parameters are well-defined with JSON Schema
3. **Improved Performance**: Direct function calls instead of parsing natural language
4. **Better Error Handling**: Structured error responses
5. **Easier Testing**: Functions can be tested independently

## Getting Help

If you need help migrating your code or have questions, please:

1. Check the [function calling documentation](../llms/custom-llm-configs.md)
2. Open an issue on GitHub if you encounter problems
3. Join our community Discord for support