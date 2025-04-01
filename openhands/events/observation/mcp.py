from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class MCPCallToolObservation(Observation):
    observation: str = ObservationType.MCP_CALL_TOOL

    @property
    def message(self) -> str:
        return self.content
