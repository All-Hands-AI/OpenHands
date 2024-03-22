import asyncio

from opendevin.lib.command_manager import CommandManager
from opendevin.lib.event import Event

def print_callback(event):
    print(event.str_truncated(), flush=True)

class AgentController:
    def __init__(self, agent, workdir, max_iterations=100, callbacks=[]):
        self.agent = agent
        self.max_iterations = max_iterations
        self.background_commands = []
        self.command_manager = CommandManager(workdir)
        self.callbacks = callbacks
        self.callbacks.append(self.agent.add_event)
        self.callbacks.append(print_callback)

    async def add_user_event(self, event: Event):
        await self.handle_action(event)

    async def start_loop(self):
        for i in range(self.max_iterations):
            await asyncio.sleep(0.001) # Give back control for a tick, so we can await in callbacks
            print("STEP", i, flush=True)
            done = await self.step()
            if done:
                print("FINISHED", flush=True)
                break

    async def step(self) -> bool:
        log_events = self.command_manager.get_background_events()
        for event in log_events:
            self.run_callbacks(event)

        action_event = self.agent.step(self.command_manager)
        if action_event is None:
            raise Exception("Agent did not return an action event")

        await self.handle_action(action_event)
        return action_event.action == 'finish'

    async def handle_action(self, event: Event):
        print("=== HANDLING EVENT ===", flush=True)
        self.run_callbacks(event)
        print("---  EVENT OUTPUT  ---", flush=True)
        output_event = event.run(self)
        self.run_callbacks(output_event)

    def run_callbacks(self, event):
        if event is None:
            return
        for callback in self.callbacks:
            callback(event)
