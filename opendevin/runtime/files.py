from typing import Any


class WorkspaceFile:
    name: str
    children: list['WorkspaceFile']

    def __init__(self, name: str, children: list['WorkspaceFile']):
        self.name = name
        self.children = children

    def to_dict(self) -> dict[str, Any]:
        """Converts the File object to a dictionary.

        Returns:
            The dictionary representation of the File object.
        """
        return {
            'name': self.name,
            'children': [child.to_dict() for child in self.children],
        }
