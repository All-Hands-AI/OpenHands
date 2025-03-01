from dataclasses import dataclass, field
from enum import Enum

from openhands.core.schema import ObservationType
from openhands.events.observation.observation import Observation


class RecallType(Enum):
    """The type of information that can be recalled."""

    ENVIRONMENT_INFO = 'environment_info'
    """environment information (repo instructions, runtime, etc.)"""

    KNOWLEDGE_MICROAGENT = 'knowledge_microagent'
    """A knowledge microagent."""

    DEFAULT = 'default'
    """Anything else that doesn't fit into the other categories."""


@dataclass
class AgentStateChangedObservation(Observation):
    """This data class represents the result from delegating to another agent"""

    agent_state: str
    observation: str = ObservationType.AGENT_STATE_CHANGED

    @property
    def message(self) -> str:
        return ''


@dataclass
class AgentCondensationObservation(Observation):
    """The output of a condensation action."""

    observation: str = ObservationType.CONDENSE

    @property
    def message(self) -> str:
        return self.content


@dataclass
class AgentThinkObservation(Observation):
    """The output of a think action.

    In practice, this is a no-op, since it will just reply a static message to the agent
    acknowledging that the thought has been logged.
    """

    observation: str = ObservationType.THINK

    @property
    def message(self) -> str:
        return self.content


@dataclass
class RecallObservation(Observation):
    """The output of a recall action from an agent or from the environment (automatic memory operations)."""

    observation: str = ObservationType.RECALL
    recall_type: RecallType = RecallType.DEFAULT

    # For environment_info
    repo_name: str = ''
    repo_directory: str = ''
    repo_instructions: str = ''
    runtime_hosts: dict[str, int] = field(default_factory=dict)

    # For knowledge_microagent
    triggered_agents: list[dict[str, str]] = field(default_factory=list)

    @property
    def message(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        # Build a string representation of all fields
        fields = [
            f'recall_type={self.recall_type}',
            f'repo_name={self.repo_name}',
            f'repo_instructions={self.repo_instructions[:20]}...',
            f'runtime_hosts={self.runtime_hosts}',
            f'triggered_agents={self.triggered_agents}',
        ]
        return f'Recalled: {", ".join(fields)}'
