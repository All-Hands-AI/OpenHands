

from dataclasses import dataclass
from openhands.events.action.action import Action


@dataclass
class CreatePRAction(Action):
    name: str
    source_branch: str
    target_branch: str

    @property
    def message(self) -> str:
        return f'Create PR for: {self.source_branch} to {self.target_branch}'
    
    def __str__(self) -> str:
        ret = '**CreatePRAction**\n'
        ret += f'SOURCE: {self.source_branch}\nTARGET: {self.target_branch}'
        return ret