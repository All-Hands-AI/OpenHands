import asyncio
from typing import List, Callable, Tuple
import traceback

from opendevin.state import State
from opendevin.agent import Agent
from opendevin.action import (
    Action,
    NullAction,
    FileReadAction,
    FileWriteAction,
    AgentFinishAction,
)
from opendevin.observation import (
    Observation,
    AgentErrorObservation,
    NullObservation
)


from .command_manager import CommandManager

def print_with_indent(text: str):
    print("\t"+text.replace("\n","\n\t"), flush=True)

class AgentController:
    def __init__(
        self,
        agent: Agent,
        workdir: str,
        max_iterations: int = 100,
        callbacks: List[Callable] = [],
    ):
        self.agent = agent
        self.max_iterations = max_iterations
        self.workdir = workdir
        self.command_manager = CommandManager(workdir)
        self.callbacks = callbacks
        self.state_updated_info: List[Tuple[Action, Observation]] = []

    def get_current_state(self) -> State:
        # update observations & actions
        state = State(
            background_commands_obs=self.command_manager.get_background_obs(),
            updated_info=self.state_updated_info,
        )
        self.state_updated_info = []
        return state

    def add_history(self, action: Action, observation: Observation):
        if not isinstance(action, Action):
            raise ValueError("action must be an instance of Action")
        if not isinstance(observation, Observation):
            raise ValueError("observation must be an instance of Observation")
        self.state_updated_info.append((action, observation))

    async def start_loop(self, task_instruction: str):
        finished = False
        self.agent.instruction = task_instruction
        for i in range(self.max_iterations):
            try:
                finished = await self.step(i)
            except Exception as e:
                print("Error in loop", e, flush=True)
                traceback.print_exc()
                break
            if finished:
                break
        if not finished:
            print("Exited before finishing", flush=True)

    async def step(self, i: int):
        print("\n\n==============", flush=True)
        print("STEP", i, flush=True)
        log_obs = self.command_manager.get_background_obs()
        for obs in log_obs:
            self.add_history(NullAction(), obs)
            await self._run_callbacks(obs)
            print_with_indent("\nBACKGROUND LOG:\n%s" % obs)

        state: State = self.get_current_state()
        action: Action = NullAction()
        observation: Observation = NullObservation("")
        try:
            action = self.agent.step(state)
            print_with_indent("\nACTION:\n%s" % action)
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            print_with_indent("\nAGENT ERROR:\n%s" % observation)
            traceback.print_exc()

        await self._run_callbacks(action)

        if isinstance(action, AgentFinishAction):
            print_with_indent("\nFINISHED")
            return True
        if isinstance(action, (FileReadAction, FileWriteAction)):
            action_cls = action.__class__
            _kwargs = action.__dict__
            _kwargs["base_path"] = self.workdir
            action = action_cls(**_kwargs)
            print(action, flush=True)
        if action.executable:
            observation = action.run(self)

        if not isinstance(observation, NullObservation):
            print_with_indent("\nOBSERVATION:\n%s" % observation)

        self.add_history(action, observation)
        await self._run_callbacks(observation)

    async def _run_callbacks(self, event):
        if event is None:
            return
        for callback in self.callbacks:
            idx = self.callbacks.index(callback)
            try:
                callback(event)
            except Exception as e:
                print("Callback error:" + str(idx), e, flush=True)
                pass
        await asyncio.sleep(0.001) # Give back control for a tick, so we can await in callbacks
