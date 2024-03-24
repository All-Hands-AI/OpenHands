from typing import List

from opendevin.state import State
from opendevin.agent import Agent
from opendevin.action import (
    Action,
    FileReadAction,
    FileWriteAction,
    AgentFinishAction,
)
from opendevin.observation import (
    Observation,
)


from .command_manager import CommandManager


def print_callback(event):
    print(event, flush=True)


class AgentController:
    def __init__(
        self,
        agent: Agent,
        workdir: str,
        max_iterations: int = 100,
    ):
        self.agent = agent
        self.max_iterations = max_iterations
        self.workdir = workdir
        self.command_manager = CommandManager(workdir)
        self.state_updated_info: List[Action | Observation] = []

    def get_current_state(self) -> State:
        # update observations & actions
        state = State(
            background_commands_obs=self.command_manager.get_background_obs(),
            updated_info=self.state_updated_info,
        )
        self.state_updated_info = []
        return state

    def start_loop(self):
        for i in range(self.max_iterations):
            print("STEP", i, flush=True)

            state: State = self.get_current_state()
            action: Action = self.agent.step(state)
            self.state_updated_info.append(action)
            print("ACTION", action, flush=True)
            
            if isinstance(action, AgentFinishAction):
                break
            if isinstance(action, (FileReadAction, FileWriteAction)):
                action_cls = action.__class__
                _kwargs = action.__dict__
                _kwargs["workspace_dir"] = self.workdir
                action = action_cls(**_kwargs)
                print(action, flush=True)
            print("---", flush=True)


            if action.executable:
                observation: Observation = action.run(self)
                self.state_updated_info.append(observation)
                print(observation, flush=True)
            else:
                print("ACTION NOT EXECUTABLE", flush=True)

            print("==============", flush=True)
