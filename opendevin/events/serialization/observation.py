from opendevin.events.observation.agent import AgentStateChangedObservation
from opendevin.events.observation.browse import BrowserOutputObservation
from opendevin.events.observation.commands import (
    CmdOutputObservation,
    IPythonRunCellObservation,
)
from opendevin.events.observation.delegate import AgentDelegateObservation
from opendevin.events.observation.empty import NullObservation
from opendevin.events.observation.error import ErrorObservation
from opendevin.events.observation.files import FileReadObservation, FileWriteObservation
from opendevin.events.observation.observation import Observation
from opendevin.events.observation.recall import AgentRecallObservation
from opendevin.events.observation.success import SuccessObservation

observations = (
    NullObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
    BrowserOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    AgentRecallObservation,
    AgentDelegateObservation,
    SuccessObservation,
    ErrorObservation,
    AgentStateChangedObservation,
)

OBSERVATION_TYPE_TO_CLASS = {
    observation_class.observation: observation_class  # type: ignore[attr-defined]
    for observation_class in observations
}


def observation_from_dict(observation: dict) -> Observation:
    observation = observation.copy()
    if 'observation' not in observation:
        raise KeyError(f"'observation' key is not found in {observation=}")
    observation_class = OBSERVATION_TYPE_TO_CLASS.get(observation['observation'])
    if observation_class is None:
        raise KeyError(
            f"'{observation['observation']=}' is not defined. Available observations: {OBSERVATION_TYPE_TO_CLASS.keys()}"
        )
    observation.pop('observation')
    observation.pop('message', None)
    content = observation.pop('content', '')
    extras = observation.pop('extras', {})
    return observation_class(content=content, **extras)
