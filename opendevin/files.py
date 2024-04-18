from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel


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


def get_folder_structure(workdir: Path) -> WorkspaceFile:
    """Gets the folder structure of a directory.

    Args:
        workdir: The directory path.

    Returns:
        The folder structure.
    """
    root = WorkspaceFile(name=workdir.name, children=[])
    for item in workdir.iterdir():
        if item.is_dir():
            dir = get_folder_structure(item)
            if dir.children:
                root.children.append(dir)
        else:
            root.children.append(WorkspaceFile(name=item.name, children=[]))
    return root


class WorkspaceItem(BaseModel):
    name: str
    isBranch: bool
    relativePath: str
    id: str
    parent: str | None
    children: List['WorkspaceItem'] = []


def get_single_level_folder_structure(base_path: Path, workdir: Path) -> List[WorkspaceItem]:
    """Generate a list of files and directories at the current level with type indicator, relative paths, and tree metadata."""
    entries = []
    for item in workdir.iterdir():
        item_relative_path = item.relative_to(base_path).as_posix()
        # Using the relative path as an 'id' ensuring uniqueness within the workspace context
        parent_path = workdir.relative_to(base_path).as_posix() if workdir != base_path else 'root'
        entries.append(WorkspaceItem(
            name=item.name,
            isBranch=item.is_dir(),
            relativePath=item_relative_path,
            id=item_relative_path,
            parent=parent_path
        ))
    return entries
