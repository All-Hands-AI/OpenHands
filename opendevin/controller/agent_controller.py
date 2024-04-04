
import asyncio
import inspect
import traceback
from typing import List, Callable, Literal, Mapping, Awaitable, Any, cast

from termcolor import colored

from opendevin.plan import Plan
from opendevin.state import State
from opendevin.agent import Agent
from opendevin.action import (
    Action,
    NullAction,
    AgentFinishAction,
    AddTaskAction,
    ModifyTaskAction
)
from opendevin.observation import (
    Observation,
    AgentErrorObservation,
    NullObservation
)
from opendevin import config

from .command_manager import CommandManager


ColorType = Literal['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'light_grey', 'dark_grey', 'light_red', 'light_green', 'light_yellow', 'light_blue', 'light_magenta', 'light_cyan', 'white']

DISABLE_COLOR_PRINTING = config.get_or_default("DISABLE_COLOR", "false").lower() == "true"
MAX_ITERATIONS = config.get("MAX_ITERATIONS")

def print_with_color(text: Any, print_type: str = "INFO"):
    TYPE_TO_COLOR: Mapping[str, ColorType] = {
        "BACKGROUND LOG": "blue",
        "ACTION": "green",
        "OBSERVATION": "yellow",
        "INFO": "cyan",
        "ERROR": "red",
        "PLAN": "light_magenta",
    }
    color = TYPE_TO_COLOR.get(print_type.upper(), TYPE_TO_COLOR["INFO"])
    if DISABLE_COLOR_PRINTING:
        print(f"\n{print_type.upper()}:\n{str(text)}", flush=True)
    else:
        print(
            colored(f"\n{print_type.upper()}:\n", color, attrs=["bold"])
            + colored(str(text), color),
            flush=True,
        )

class AgentController:
    def __init__(
        self,
        agent: Agent,
        workdir: str,
        max_iterations: int = MAX_ITERATIONS,
        container_image: str | None = None,
        callbacks: List[Callable] = [],
    ):
        self.agent = agent
        self.max_iterations = max_iterations
        self.workdir = workdir
        self.command_manager = CommandManager(workdir,container_image)
        self.callbacks = callbacks

    def update_state_for_step(self, i):
        self.state.iteration = i
        self.state.background_commands_obs = self.command_manager.get_background_obs()

    def update_state_after_step(self):
        self.state.updated_info = []

    def add_history(self, action: Action, observation: Observation):
        if not isinstance(action, Action):
            raise ValueError("action must be an instance of Action")
        if not isinstance(observation, Observation):
            raise ValueError("observation must be an instance of Observation")
        self.state.history.append((action, observation))
        self.state.updated_info.append((action, observation))

    async def start_loop(self, task: str):
        finished = False
        plan = Plan(task)
        self.state = State(plan)
        for i in range(self.max_iterations):
            try:
                finished = await self.step(i)
            except Exception as e:
                print("Error in loop", e, flush=True)
                raise e
            if finished:
                break
        if not finished:
            print("Exited before finishing", flush=True)

    async def step(self, i: int):
        print("\n\n==============", flush=True)
        print("STEP", i, flush=True)
        print_with_color(self.state.plan.main_goal, "PLAN")

        log_obs = self.command_manager.get_background_obs()
        for obs in log_obs:
            self.add_history(NullAction(), obs)
            await self._run_callbacks(obs)
            print_with_color(obs, "BACKGROUND LOG")

        self.update_state_for_step(i)
        action: Action = NullAction()
        observation: Observation = NullObservation("")
        try:
            action = self.agent.step(self.state)
            if action is None:
                raise ValueError("Agent must return an action")
            print_with_color(action, "ACTION")
        except Exception as e:
            observation = AgentErrorObservation(str(e))
            print_with_color(observation, "ERROR")
            traceback.print_exc()
            # TODO Change to more robust error handling
            if "The api_key client option must be set" in observation.content:
                raise 
        self.update_state_after_step()

        await self._run_callbacks(action)

        finished = isinstance(action, AgentFinishAction)
        if finished:
            print_with_color(action, "INFO")
            return True

        if isinstance(action, AddTaskAction):
            try:
                self.state.plan.add_subtask(action.parent, action.goal, action.subtasks)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, "ERROR")
                traceback.print_exc()
        elif isinstance(action, ModifyTaskAction):
            try:
                self.state.plan.set_subtask_state(action.id, action.state)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, "ERROR")
                traceback.print_exc()

        if action.executable:
            try:
                if inspect.isawaitable(action.run(self)):
                    observation = await cast(Awaitable[Observation], action.run(self))
                else:
                    observation = action.run(self)
            except Exception as e:
                observation = AgentErrorObservation(str(e))
                print_with_color(observation, "ERROR")
                traceback.print_exc()

        if not isinstance(observation, NullObservation):
            print_with_color(observation, "OBSERVATION")

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
