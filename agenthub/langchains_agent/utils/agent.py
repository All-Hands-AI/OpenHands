from agenthub.langchains_agent.utils.monologue import Monologue
from agenthub.langchains_agent.utils.memory import LongTermMemory
from opendevin.lib.event import Event
import agenthub.langchains_agent.utils.llm as llm

MAX_OUTPUT_LENGTH = 5000
MAX_MONOLOGUE_LENGTH = 20000

class Agent:
    def __init__(self, task, model_name):
        self.task = task
        self.model_name = model_name
        self.monologue = Monologue(model_name)
        self.memory = LongTermMemory()

    def add_event(self, event):
        if 'output' in event.args and len(event.args['output']) > MAX_OUTPUT_LENGTH:
            event.args['output'] = event.args['output'][:MAX_OUTPUT_LENGTH] + "..."
        self.monologue.add_event(event)
        self.memory.add_event(event)
        if self.monologue.get_total_length() > MAX_MONOLOGUE_LENGTH:
            self.monologue.condense()

    def get_next_action(self, cmd_mgr):
        action_dict = llm.request_action(
            self.task,
            self.monologue.get_thoughts(),
            self.model_name,
            cmd_mgr.background_commands
        )
        if action_dict is None:
            # TODO: this seems to happen if the LLM response isn't valid JSON. Maybe it should be an `error` instead? How should we handle this case?
            return Event('think', {'thought': '...'})
        event = Event(action_dict['action'], action_dict['args'])
        self.latest_action = event
        return event

