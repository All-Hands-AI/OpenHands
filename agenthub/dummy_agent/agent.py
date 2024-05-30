import time
from typing import TypedDict

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.events.action import (
    Action,
    AddTaskAction,
    AgentFinishAction,
    AgentRecallAction,
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
    AgentRecallObservation,
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
* command_id is sometimes a number, sometimes a string
* Why isn't the output of the background command split between two steps?
* Browser not working
"""

ActionObs = TypedDict(
    'ActionObs', {'action': Action, 'observations': list[Observation]}
)

BACKGROUND_CMD = 'echo "This is in the background" && sleep .1 && echo "This too"'


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
                'action': CmdRunAction(command=BACKGROUND_CMD, background=True),
                'observations': [
                    CmdOutputObservation(
                        'Background command started. To stop it, send a `kill` action with command_id 42',
                        command_id='42',  # type: ignore[arg-type]
                        command=BACKGROUND_CMD,
                    ),
                    CmdOutputObservation(
                        'This is in the background\nThis too\n',
                        command_id='42',  # type: ignore[arg-type]
                        command=BACKGROUND_CMD,
                    ),
                ],
            },
            {
                'action': AgentRecallAction(query='who am I?'),
                'observations': [
                    AgentRecallObservation('', memories=['I am a computer.']),
                    # CmdOutputObservation('This too\n', command_id='42', command=BACKGROUND_CMD),
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
            if 'observations' in prev_step:
                expected_observations = prev_step['observations']
                hist_start = len(state.history) - len(expected_observations)
                for i in range(len(expected_observations)):
                    hist_obs = event_to_dict(state.history[hist_start + i][1])
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
                    if hist_obs != expected_obs:
                        print('\nactual', hist_obs)
                        print('\nexpect', expected_obs)
                    assert (
                        hist_obs == expected_obs
                    ), f'Expected observation {expected_obs}, got {hist_obs}'
        return self.steps[state.iteration]['action']

    def search_memory(self, query: str) -> list[str]:
        return ['I am a computer.']
