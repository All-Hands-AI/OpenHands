from .base import NullObservation, Observation
from .browse import BrowserOutputObservation
from .delegate import AgentDelegateObservation
from .error import AgentErrorObservation
from .files import FileReadObservation, FileWriteObservation
from .message import AgentMessageObservation, UserMessageObservation
from .recall import AgentRecallObservation
from .run import CmdOutputObservation, IPythonRunCellObservation

observations = (
    CmdOutputObservation,
    BrowserOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    UserMessageObservation,
    AgentMessageObservation,
    AgentRecallObservation,
    AgentDelegateObservation,
    AgentErrorObservation,
)

OBSERVATION_TYPE_TO_CLASS = {observation_class.observation: observation_class for observation_class in observations}  # type: ignore[attr-defined]


def observation_from_dict(observation: dict) -> Observation:
    observation = observation.copy()
    if 'observation' not in observation:
        raise KeyError(f"'observation' key is not found in {observation=}")
    observation_class = OBSERVATION_TYPE_TO_CLASS.get(observation['observation'])
    if observation_class is None:
        raise KeyError(f"'{observation['observation']=}' is not defined. Available observations: {OBSERVATION_TYPE_TO_CLASS.keys()}")
    observation.pop('observation')
    observation.pop('message', None)
    content = observation.pop('content', '')
    extras = observation.pop('extras', {})
    return observation_class(content=content, **extras)


__all__ = [
    'Observation',
    'NullObservation',
    'CmdOutputObservation',
    'IPythonRunCellObservation',
    'BrowserOutputObservation',
    'FileReadObservation',
    'FileWriteObservation',
    'UserMessageObservation',
    'AgentMessageObservation',
    'AgentRecallObservation',
    'AgentErrorObservation',
]
