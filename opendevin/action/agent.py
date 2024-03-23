from dataclasses import dataclass

from .base import Action
from ..controller import AgentController


@dataclass
class AgentRecallAction(Action):
    pass

    def run(self, controller: AgentController) -> str:
        return controller.agent.search_memory(self.args['query'])

