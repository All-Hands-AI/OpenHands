from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opendevin.controller import AgentController


@dataclass
class Action:
    def run(self, controller: "AgentController") -> str:
        raise NotImplementedError

    def to_dict(self):
        return {"action_type": self.__class__.__name__, "args": self.__dict__}

    @property
    def executable(self) -> bool:
        raise NotImplementedError



class ExecutableAction(Action):
    @property
    def executable(self) -> bool:
        return True


class NotExecutableAction(Action):
    @property
    def executable(self) -> bool:
        return False
