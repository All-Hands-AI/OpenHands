from dataclasses import dataclass
from typing import Any

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


@dataclass
class MCPCallToolObservation(Observation):
    observation: str = ObservationType.MCP_CALL_TOOL
    tool_name: str = ''
    kwargs: dict[str, Any] | None = None

    @property
    def message(self) -> str:
        return self.content
