from typing import List, Callable

from opendevin.lib.event import Event
from opendevin.state import State
from opendevin.agent import Agent
from opendevin.action import Action

from .command_manager import CommandManager


def print_callback(event):
    print(event, flush=True)


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
        self.background_commands = []
        self.command_manager = CommandManager(workdir)

        self.callbacks = callbacks
        self.callbacks.append(self.agent.add_event)
        self.callbacks.append(print_callback)

    def maybe_perform_action(self, event):
        if not (event and event.is_runnable()):
            return
        action = "output"
        try:
            output = event.run(self)
        except Exception as e:
            output = "Error: " + str(e)
            action = "error"
        out_event = Event(action, {"output": output})
        return out_event

    @property
    def state(self) -> State:
        return State(background_commands=self.command_manager.background_commands)

    def start_loop(self):
        for i in range(self.max_iterations):
            print("STEP", i, flush=True)
            log_events = self.command_manager.get_background_events()
            for event in log_events:
                for callback in self.callbacks:
                    callback(event)

            action: Action = self.agent.step(self.state)
            for callback in self.callbacks:
                callback(action_event)
            if action_event.action == "finish":
                break
            print("---", flush=True)

            output_event = self.maybe_perform_action(action_event)
            if output_event is not None:
                for callback in self.callbacks:
                    callback(output_event)
            print("==============", flush=True)
