from dataclasses import dataclass

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class MCPObservation(Observation):
    """This data class represents the result of a MCP Server operation."""

    observation: str = ObservationType.MCP
    name: str = ''  # The name of the MCP tool that was called

    @property
    def message(self) -> str:
        return self.content
