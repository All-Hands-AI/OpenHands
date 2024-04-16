from pathlib import Path
from typing import Any, Dict, List


class WorkspaceFile:
    name: str
    children: List['WorkspaceFile']

    def __init__(self, name: str, children: List['WorkspaceFile']):
        self.name = name
        self.children = children

    def to_dict(self) -> Dict[str, Any]:
        """Converts the File object to a dictionary.

        Returns:
            The dictionary representation of the File object.
        """
        return {
            'name': self.name,
            'children': [child.to_dict() for child in self.children],
        }


def get_folder_structure(base_path: Path, prefix: str | None = None, depth=None) -> WorkspaceFile:
    """Gets the folder structure of a directory up to a specified depth, validating the path and checking for existence.

    Args:
        base_path: The base directory path.
        prefix: Optional path prefix relative to the base path.
        depth: Optional; the maximum depth to recurse, if None, it recurses fully.

    Returns:
        The folder structure.
    """
    # Construct the full path
    full_path = base_path / prefix if prefix else base_path
    full_path = full_path.resolve()

    # Validate that the resolved path does not escape the base directory and exists
    if not str(full_path).startswith(str(base_path)) or not full_path.exists():
        raise ValueError('Invalid or non-existent path provided.')

    root = WorkspaceFile(name=full_path.name, children=[])
    if depth is None or depth > 0:
        new_depth = None if depth is None else depth - 1
        for item in full_path.iterdir():
            if item.is_dir():
                dir = get_folder_structure(item, depth=new_depth)
                if dir.children:
                    root.children.append(dir)
            else:
                root.children.append(WorkspaceFile(name=item.name, children=[]))
    return root
