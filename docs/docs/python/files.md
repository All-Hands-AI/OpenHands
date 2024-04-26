---
sidebar_label: files
title: files
---

## WorkspaceFile Objects

```python
class WorkspaceFile()
```

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

Converts the File object to a dictionary.

**Returns**:

  The dictionary representation of the File object.

#### get\_folder\_structure

```python
def get_folder_structure(workdir: Path) -> WorkspaceFile
```

Gets the folder structure of a directory.

**Arguments**:

- `workdir` - The directory path.
  

**Returns**:

  The folder structure.

