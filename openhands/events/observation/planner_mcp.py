from dataclasses import dataclass
from typing import Dict, List

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation

# @dataclass
# class Task:
#     """A task in a plan."""

#     content: str
#     status: str = 'not_started'
#     result: str = ''


@dataclass
class PlanObservation(Observation):
    """This data class represents the result of a Planner agent create plan operation."""

    plan_id: str
    title: str
    tasks: List[Dict]
    content: str
    observation: str = ObservationType.MCP_PLAN

    @property
    def message(self) -> str:
        return self.content
