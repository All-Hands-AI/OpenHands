from typing import TypedDict

from openhands.controller.agent import Agent
from openhands.controller.state.state import State
from openhands.core.config import AgentConfig
from openhands.core.schema import AgentState
from openhands.events.action import (
    Action,
    AgentFinishAction,
    AgentRejectAction,
    BrowseInteractiveAction,
    BrowseURLAction,
    CmdRunAction,
    FileReadAction,
    FileWriteAction,
    MessageAction,
)
from openhands.events.observation import (
    AgentStateChangedObservation,
    BrowserOutputObservation,
    CmdOutputMetadata,
    CmdOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    Observation,
)
from openhands.events.serialization.event import event_to_dict
from openhands.llm.llm import LLM

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

    def __init__(self, llm: LLM, config: AgentConfig):
        super().__init__(llm, config)
        self.steps: list[ActionObs] = [
            {
                'action': MessageAction('Time to get started!'),
                'observations': [],
            },
            {
                'action': CmdRunAction(command='echo "foo"'),
                'observations': [CmdOutputObservation('foo', command='echo "foo"')],
            },
            {
                'action': FileWriteAction(
                    content='echo "Hello, World!"', path='hello.sh'
                ),
                'observations': [
                    FileWriteObservation(
                        content='echo "Hello, World!"', path='hello.sh'
                    )
                ],
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
                        'bash: hello.sh: No such file or directory',
                        command='bash workspace/hello.sh',
                        metadata=CmdOutputMetadata(exit_code=127),
                    )
                ],
            },
            {
                'action': BrowseURLAction(url='https://google.com'),
                'observations': [
                    BrowserOutputObservation(
                        '<html><body>Simulated Google page</body></html>',
                        url='https://google.com',
                        screenshot='',
                        trigger_by_action='',
                    ),
                ],
            },
            {
                'action': BrowseInteractiveAction(
                    browser_actions='goto("https://google.com")'
                ),
                'observations': [
                    BrowserOutputObservation(
                        '<html><body>Simulated Google page after interaction</body></html>',
                        url='https://google.com',
                        screenshot='',
                        trigger_by_action='',
                    ),
                ],
            },
            {
                'action': AgentRejectAction(),
                'observations': [AgentStateChangedObservation('', AgentState.REJECTED)],
            },
            {
                'action': AgentFinishAction(
                    outputs={}, thought='Task completed', action='finish'
                ),
                'observations': [AgentStateChangedObservation('', AgentState.FINISHED)],
            },
        ]

    def step(self, state: State) -> Action:
        if state.iteration_flag.current_value >= len(self.steps):
            return AgentFinishAction()

        current_step = self.steps[state.iteration_flag.current_value]
        action = current_step['action']

        if state.iteration_flag.current_value > 0:
            prev_step = self.steps[state.iteration_flag.current_value - 1]

            if 'observations' in prev_step and prev_step['observations']:
                expected_observations = prev_step['observations']
                hist_events = state.view[-len(expected_observations) :]

                if len(hist_events) < len(expected_observations):
                    print(
                        f'Warning: Expected {len(expected_observations)} observations, but got {len(hist_events)}'
                    )

                for i in range(min(len(expected_observations), len(hist_events))):
                    hist_obs = event_to_dict(hist_events[i])
                    expected_obs = event_to_dict(expected_observations[i])

                    # Remove dynamic fields for comparison
                    for obs in [hist_obs, expected_obs]:
                        obs.pop('id', None)
                        obs.pop('timestamp', None)
                        obs.pop('cause', None)
                        obs.pop('source', None)

                    if hist_obs != expected_obs:
                        print(
                            f'Warning: Observation mismatch. Expected {expected_obs}, got {hist_obs}'
                        )

        return action
