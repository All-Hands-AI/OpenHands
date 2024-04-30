---
sidebar_label: fileop
title: opendevin.action.fileop
---

## FileReadAction Objects

```python
@dataclass
class FileReadAction(ExecutableAction)
```

Reads a file from a given path.
Can be set to read specific lines using start and end
Default lines 0:-1 (whole file)

