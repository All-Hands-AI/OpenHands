import agenthub.langchains_agent.utils.json as json
from opendevin.lib.event import Event

import agenthub.langchains_agent.utils.llm as llm

class Monologue:
    def __init__(self, model_name):
        self.thoughts = []
        self.model_name = model_name

    def add_event(self, t):
        self.thoughts.append(t)

    def get_thoughts(self):
        return self.thoughts

    def get_total_length(self):
        return sum([len(json.dumps(t)) for t in self.thoughts])

    def condense(self):
        new_thoughts = llm.summarize_monologue(self.thoughts, self.model_name)
        print("new thoughts", new_thoughts)
        self.thoughts = [Event(t['action'], t['args']) for t in new_thoughts]


