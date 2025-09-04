# Encoding Migration Guide

This guide helps developers migrate existing file I/O code to the unified encoding utilities.

## Quick Migration

### 1. Import the unified encoding helpers

```python
from openhands.utils.encoding import safe_read, safe_write, safe_open
```

### 2. Replace existing file operations

#### Read text files
```python
# Old
with open(file_path, 'r') as f:
    content = f.read()

# New
content = safe_read(file_path)
```

#### Write text files
```python
# Old
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# New
safe_write(file_path, content)
```

#### Open files
```python
# Old
with open(file_path, 'r', encoding='utf-8') as f:
    # process file

# New
with safe_open(file_path, 'r') as f:
    # process file
```

## Advanced Usage

### 1. Custom encodings
```python
from openhands.utils.encoding import open_text_file, read_text_file

# Specify an explicit encoding
with open_text_file(file_path, 'r', encoding='gbk') as f:
    content = f.read()

# Provide custom fallback encodings
content = read_text_file(file_path, fallback_encodings=['utf-8', 'latin-1'])
```

### 2. Configuration management
```python
from openhands.core.encoding_config import encoding_config

# Read current config
default_encoding = encoding_config.get_preferred_encoding()
fallback_encodings = encoding_config.get_fallback_encodings()

# Check encoding support
if encoding_config.is_encoding_supported('gbk'):
    # use GBK if needed
    pass
```

## Migration Checklist

- [ ] Import the unified encoding helpers
- [ ] Replace all direct `open()` calls
- [ ] Remove hard-coded encoding arguments
- [ ] Test cross-platform (Windows/Linux/macOS)
- [ ] Update docs and comments

## FAQ

### Q: Why unify encoding configuration?
A: To ensure cross-platform compatibility, simplify maintenance, provide consistent error handling, and support multiple fallback encodings.

### Q: How to handle files with special encodings?
A: Use `read_text_file()`, which tries multiple encodings automatically:
```python
from openhands.utils.encoding import read_text_file

# Try multiple encodings automatically
content = read_text_file(file_path)
```

### Q: How to add support for a new encoding?
A: Modify the `FALLBACK_ENCODINGS` list in `encoding_config.py`:
```python
FALLBACK_ENCODINGS = [
    'utf-8-sig',
    'latin-1',
    'cp1252',
    'gbk',
    'your-new-encoding',  # add new encoding here
]
```

## Performance Notes

- `safe_read()` and `safe_write()` are optimized; overhead is minimal.
- Encoding detection is only attempted after the first failure.
- Binary file operations are unaffected.
