import asyncio
from pathlib import Path
from typing import TypedDict, Union

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
    BrowserOutputObservation,
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
                'action': AddTaskAction(
                    parent='None', goal='check the current directory'
                ),
                'observations': [],
            },
            {
                'action': AddTaskAction(parent='0', goal='run ls'),
                'observations': [NullObservation('')],
            },
            {
                'action': ModifyTaskAction(task_id='0', state='in_progress'),
                'observations': [NullObservation('')],
            },
            {
                'action': MessageAction('Time to get started!'),
                'observations': [NullObservation('')],
            },
            {
                'action': CmdRunAction(command='echo "foo"'),
                'observations': [
                    CmdOutputObservation(
                        'foo', command_id=-1, command='echo "foo"', exit_code=0
                    )
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
                'action': AgentRecallAction(query='who am I?'),
                'observations': [
                    AgentRecallObservation('', memories=['I am a computer.']),
                ],
            },
            {
                'action': BrowseURLAction(url='https://google.com'),
                'observations': [
                    BrowserOutputObservation(
                        '<html><body>Simulated Google page</body></html>',
                        url='https://google.com',
                        screenshot='',
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
                    ),
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
        return asyncio.run(self.async_step(state))

    async def async_step(self, state: State) -> Action:
        await asyncio.sleep(0.1)
        if state.iteration >= len(self.steps):
            return AgentFinishAction()

        current_step = self.steps[state.iteration]
        action = current_step['action']

        # If the action is AddTaskAction or ModifyTaskAction, update the parent ID or task_id
        if isinstance(action, AddTaskAction):
            if action.parent == 'None':
                action.parent = ''  # Root task has no parent
            elif action.parent == '0':
                action.parent = state.root_task.id
            elif action.parent.startswith('0.'):
                action.parent = f'{state.root_task.id}{action.parent[1:]}'
        elif isinstance(action, ModifyTaskAction):
            if action.task_id == '0':
                action.task_id = state.root_task.id
            elif action.task_id.startswith('0.'):
                action.task_id = f'{state.root_task.id}{action.task_id[1:]}'
            # Ensure the task_id doesn't start with a dot
            if action.task_id.startswith('.'):
                action.task_id = action.task_id[1:]
        elif isinstance(action, (FileWriteAction, FileReadAction)):
            # Await the working directory before creating the FileWriteAction or FileReadAction
            working_directory = await self.get_working_directory(state)
            action.path = str(Path(working_directory) / action.path)
        elif isinstance(action, (BrowseURLAction, BrowseInteractiveAction)):
            return self.simulate_browser_action(action)

        if state.iteration > 0:
            prev_step = self.steps[state.iteration - 1]

            if 'observations' in prev_step and prev_step['observations']:
                expected_observations = prev_step['observations']
                hist_events = state.history.get_last_events(len(expected_observations))

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
                        if 'extras' in obs:
                            obs['extras'].pop('command_id', None)

                    if hist_obs != expected_obs:
                        print(
                            f'Warning: Observation mismatch. Expected {expected_obs}, got {hist_obs}'
                        )

        # Handle FileWriteAction
        if isinstance(action, FileWriteAction):
            action.path = str(action.path)

        # Handle BrowseURLAction and BrowseInteractiveAction
        if isinstance(action, (BrowseURLAction, BrowseInteractiveAction)):
            return self.simulate_browser_action(action)

        return action

    def simulate_browser_action(
        self, action: Union[BrowseURLAction, BrowseInteractiveAction]
    ) -> Action:  # Change return type to Action
        if isinstance(action, BrowseURLAction):
            return BrowseURLAction(url=action.url)  # Return the original action
        elif isinstance(action, BrowseInteractiveAction):
            return BrowseInteractiveAction(
                browser_actions=action.browser_actions
            )  # Return the original action
        else:
            raise ValueError('Unexpected action type for browser simulation')

    async def get_working_directory(self, state: State) -> str:
        # Implement this method to return the current working directory
        # This might involve accessing state information or making an async call
        # For now, we'll return a placeholder value
        return '/workspace'

    def search_memory(self, query: str) -> list[str]:
        return ['I am a computer.']
