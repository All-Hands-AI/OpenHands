from opendevin.schema import ActionType

from .action import Action


class NullAction(Action):
    """An action that does nothing.
    """
    action: str = ActionType.NULL

    @property
    def message(self) -> str:
        return 'No action'
