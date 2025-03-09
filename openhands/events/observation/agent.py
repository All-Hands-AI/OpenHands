from dataclasses import dataclass, field

from openhands.core.schema import ObservationType
from openhands.events.event import RecallType
from openhands.events.observation.observation import Observation


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

    # environment_info
    repo_name: str = ''
    repo_directory: str = ''
    repo_instructions: str = ''
    runtime_hosts: dict[str, int] = field(default_factory=dict)
    additional_agent_instructions: str = ''

    # microagent
    microagent_knowledge: list[dict[str, str]] = field(default_factory=list)
    """
    A list of dictionaries, each containing information about a triggered microagent.
    Each dictionary has the following keys:
        - agent_name: str - The name of the microagent that was triggered
        - trigger_word: str - The word that triggered this microagent
        - content: str - The actual content/knowledge from the microagent

    Example:
    [
        {
            "agent_name": "python_best_practices",
            "trigger_word": "python",
            "content": "Always use virtual environments for Python projects."
        },
        {
            "agent_name": "git_workflow",
            "trigger_word": "git",
            "content": "Create a new branch for each feature or bugfix."
        }
    ]
    """

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
            f'additional_agent_instructions={self.additional_agent_instructions[:20]}...',
            f'microagent_knowledge={self.microagent_knowledge}',
        ]
        return f'Recalled: {", ".join(fields)}'
