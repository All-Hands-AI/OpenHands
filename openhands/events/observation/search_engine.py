from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class SearchEngineObservation(Observation):
    query: str
    observation: str = ObservationType.SEARCH

    @property
    def message(self) -> str:
        return f'Searched for: {self.query}'

    def __str__(self) -> str:
        ret = (
            '**SearchEngineObservation**\n'
            f'Query: {self.query}\n'
            f'Search Results: {self.content}\n'
        )
        return ret
