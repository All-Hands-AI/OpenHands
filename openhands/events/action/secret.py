from dataclasses import dataclass

from openhands.core.schema import ActionType
from openhands.events.action.action import Action


@dataclass
class SearchSecretsAction(Action):
    query: str | None = None
    action: str = ActionType.SEARCH_SECRETS

    @property
    def message(self) -> str:
        return f'I am searching for secrets for: {self.query}'

    def __str__(self) -> str:
        ret = '**SearchSecretsAction**\n'
        if self.query:
            ret += f'QUERY: {self.query}\n'
        return ret
