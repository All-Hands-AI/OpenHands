from pathlib import Path
from typing import List

from pydantic import BaseModel


class WorkspaceItem(BaseModel):
    name: str
    isBranch: bool
    relativePath: str
    id: str
    parent: str | None
    children: List['WorkspaceItem'] = []


def get_single_level_folder_structure(
    base_path: Path, workdir: Path
) -> List[WorkspaceItem]:
    """Generate a list of files and directories at the current level with type indicator, relative paths, and tree metadata."""
    entries: List[WorkspaceItem] = []
    if not workdir.is_dir():
        return entries
    for item in workdir.iterdir():
        item_relative_path = item.relative_to(base_path).as_posix()
        # Using the relative path as an 'id' ensuring uniqueness within the workspace context
        parent_path = (
            workdir.relative_to(base_path).as_posix()
            if workdir != base_path
            else 'root'
        )
        entries.append(
            WorkspaceItem(
                name=item.name,
                isBranch=item.is_dir(),
                relativePath=item_relative_path,
                id=item_relative_path,
                parent=parent_path,
            )
        )
    return entries
