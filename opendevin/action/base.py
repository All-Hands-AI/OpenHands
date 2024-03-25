from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opendevin.controller import AgentController
    from opendevin.observation import Observation

class Action:
    def run(self, controller: "AgentController") -> "Observation":
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

    @property
    def executable(self) -> bool:
        raise NotImplementedError

    @property
    def message(self) -> str:
        raise NotImplementedError



class ExecutableAction(Action):
    @property
    def executable(self) -> bool:
        return True


class NotExecutableAction(Action):
    @property
    def executable(self) -> bool:
        return False

class NullAction(NotExecutableAction):
    """An action that does nothing.
    This is used when the agent need to receive user follow-up messages from the frontend.
    """

    @property
    def message(self) -> str:
        return "No action"
