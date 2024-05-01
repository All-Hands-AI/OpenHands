---
sidebar_label: files
title: opendevin.events.action.files
---

## FileReadAction Objects

```python
@dataclass
class FileReadAction(Action)
```

Reads a file from a given path.
Can be set to read specific lines using start and end
Default lines 0:-1 (whole file)

