from agenthub.langchains_agent.utils.monologue import Monologue
from agenthub.langchains_agent.utils.memory import LongTermMemory
from opendevin.lib.event import Event
import agenthub.langchains_agent.utils.llm as llm

MAX_OUTPUT_LENGTH = 5000
MAX_MONOLOGUE_LENGTH = 20000

class Agent:
    def __init__(self, task):
        self.task = task
        self.monologue = Monologue()
        self.memory = LongTermMemory()

    def add_event(self, event):
        self.monologue.add_event(event)
        self.memory.add_event(event)
        if self.monologue.get_total_length() > MAX_MONOLOGUE_LENGTH:
            self.monologue.condense()

    def get_next_action(self, cmd_mgr):
        action_dict = llm.request_action(self.task, self.monologue.get_thoughts(), cmd_mgr.background_commands)
        event = Event(action_dict['action'], action_dict['args'])
        self.latest_action = event
        return event

