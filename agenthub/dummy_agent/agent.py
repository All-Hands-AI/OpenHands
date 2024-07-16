import time
from typing import TypedDict

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import (
    Action,
    AddTaskAction,
    AgentFinishAction,
    AgentRejectAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
    ModifyTaskAction,
)
from opendevin.events.observation import (
    CmdOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    NullObservation,
    Observation,
)
from opendevin.events.serialization.event import event_to_dict
from opendevin.llm.llm import LLM

"""
FIXME: There are a few problems this surfaced
* FileWrites seem to add an unintended newline at the end of the file
* Browser not working
"""

ActionObs = TypedDict(
    'ActionObs', {'action': Action, 'observations': list[Observation]}
)


class DummyAgent(Agent):
    VERSION = '1.0'
    """
    The DummyAgent is used for e2e testing. It just sends the same set of actions deterministically,
    without making any LLM calls.
    """

    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.steps: list[ActionObs] = [
            {
                'action': AddTaskAction(parent='0', goal='check the current directory'),
                'observations': [NullObservation('')],
            },
            {
                'action': AddTaskAction(parent='0.0', goal='run ls'),
                'observations': [NullObservation('')],
            },
            {
                'action': ModifyTaskAction(task_id='0.0', state='in_progress'),
                'observations': [NullObservation('')],
            },
            {
                'action': MessageAction('Time to get started!'),
                'observations': [NullObservation('')],
            },
            {
                'action': CmdRunAction(command='echo "foo"'),
                'observations': [
                    CmdOutputObservation('foo', command_id=-1, command='echo "foo"')
                ],
            },
            {
                'action': FileWriteAction(
                    content='echo "Hello, World!"', path='hello.sh'
                ),
                'observations': [FileWriteObservation('', path='hello.sh')],
            },
            {
                'action': FileReadAction(path='hello.sh'),
                'observations': [
                    FileReadObservation('echo "Hello, World!"\n', path='hello.sh')
                ],
            },
            {
                'action': CmdRunAction(command='bash hello.sh'),
                'observations': [
                    CmdOutputObservation(
                        'Hello, World!', command_id=-1, command='bash hello.sh'
                    )
                ],
            },
            {
                'action': BrowseURLAction(url='https://google.com'),
                'observations': [
                    # BrowserOutputObservation('<html></html>', url='https://google.com', screenshot=""),
                ],
            },
            {
                'action': BrowseInteractiveAction(
                    browser_actions='goto("https://google.com")'
                ),
                'observations': [
                    # BrowserOutputObservation('<html></html>', url='https://google.com', screenshot=""),
                ],
            },
            {
                'action': AgentFinishAction(),
                'observations': [],
            },
            {
                'action': AgentRejectAction(),
                'observations': [],
            },
        ]

    def step(self, state: State) -> Action:
        time.sleep(0.1)
        if state.iteration > 0:
            prev_step = self.steps[state.iteration - 1]

            # a step is (action, observations list)
            if 'observations' in prev_step:
                # one obs, at most
                expected_observations = prev_step['observations']

                # check if the history matches the expected observations
                hist_events = state.history.get_last_events(len(expected_observations))
                for i in range(len(expected_observations)):
                    hist_obs = event_to_dict(hist_events[i])
                    expected_obs = event_to_dict(expected_observations[i])
                    if (
                        'command_id' in hist_obs['extras']
                        and hist_obs['extras']['command_id'] != -1
                    ):
                        del hist_obs['extras']['command_id']
                        hist_obs['content'] = ''
                    if (
                        'command_id' in expected_obs['extras']
                        and expected_obs['extras']['command_id'] != -1
                    ):
                        del expected_obs['extras']['command_id']
                        expected_obs['content'] = ''
                    assert (
                        hist_obs == expected_obs
                    ), f'Expected observation {expected_obs}, got {hist_obs}'
        return self.steps[state.iteration]['action']
