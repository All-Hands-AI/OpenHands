from typing import List, TypedDict

from opendevin.agent import Agent
from opendevin.llm.llm import LLM
from opendevin.state import State
from opendevin.action import (
    Action,
    CmdRunAction,
    FileWriteAction,
    FileReadAction,
    AgentFinishAction,
    AgentThinkAction,
    AddTaskAction,
    ModifyTaskAction,
    AgentRecallAction,
    BrowseURLAction,
)
from opendevin.observation import (
    Observation,
    NullObservation,
)

ActionObs = TypedDict('ActionObs', {'action': Action, 'observations': List[Observation]})


class DummyAgent(Agent):
    '''
    The DummyAgent is used for e2e testing. It just sends the same set of actions deterministically,
    without making any LLM calls.
    '''

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.steps: List[ActionObs] = [{
            'action': AddTaskAction(parent='0', goal='check the current directory'),
            'observations': [NullObservation('')],
        }, {
            'action': AddTaskAction(parent='0.0', goal='run ls'),
            'observations': [],
        }, {
            'action': ModifyTaskAction(id='0.0', state='in_progress'),
            'observations': [],
        }, {
            'action': AgentThinkAction(thought='Time to get started!'),
            'observations': [],
        }, {
            'action': CmdRunAction(command='ls'),
            'observations': [],
        }, {
            'action': FileWriteAction(content='echo "Hello, World!"', path='hello.sh'),
            'observations': [],
        }, {
            'action': FileReadAction(path='hello.sh'),
            'observations': [],
        }, {
            'action': CmdRunAction(command='bash hello.sh'),
            'observations': [],
        }, {
            'action': CmdRunAction(command='echo "This is in the background"', background=True),
            'observations': [],
        }, {
            'action': AgentRecallAction(query='who am I?'),
            'observations': [],
        }, {
            'action': BrowseURLAction(url='https://google.com'),
            'observations': [],
        }, {
            'action': AgentFinishAction(),
            'observations': [],
        }]

    def step(self, state: State) -> Action:
        if state.iteration > 0:
            prev_step = self.steps[state.iteration - 1]
            if 'observations' in prev_step:
                expected_observations = prev_step['observations']
                hist_start = len(state.history) - len(expected_observations)
                for i in range(len(expected_observations)):
                    hist_obs = state.history[hist_start + i][1]
                    expected_obs = expected_observations[i]
                    assert hist_obs == expected_obs, f'Expected observation {expected_obs}, got {hist_obs}'
        return self.steps[state.iteration]['action']

    def search_memory(self, query: str) -> List[str]:
        return ['I am a computer.']
