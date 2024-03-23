import agenthub.langchains_agent.utils.json as json
import agenthub.langchains_agent.utils.prompts as prompts

class Monologue:
    def __init__(self):
        self.thoughts = []

    def add_event(self, t: dict):
        self.thoughts.append(t)

    def get_thoughts(self):
        return self.thoughts

    def get_total_length(self):
        return sum([len(json.dumps(t)) for t in self.thoughts])

    def condense(self, llm):
        prompt = prompts.get_summarize_monologue_prompt(self.thoughts)
        response = llm.prompt(prompt)
        new_thoughts = prompts.parse_summary_response(response)
        self.thoughts = [Event(t['action'], t['args']) for t in new_thoughts]

