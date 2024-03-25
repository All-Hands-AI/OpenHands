
import agenthub.langchains_agent.utils.json as json
import agenthub.langchains_agent.utils.llm as llm

class Monologue:
    def __init__(self, model_name):
        self.thoughts = []
        self.model_name = model_name

    def add_event(self, t: dict):
        if not isinstance(t, dict):
            raise ValueError("Event must be a dictionary")
        self.thoughts.append(t)

    def get_thoughts(self):
        return self.thoughts

    def get_total_length(self):
        total_length = 0
        for t in self.thoughts:
            try:
                total_length += len(json.dumps(t))
            except TypeError as e:
                print(f"Error serializing thought: {e}")
        return total_length

    def condense(self):
        try:
            new_thoughts = llm.summarize_monologue(self.thoughts, self.model_name)
            # Ensure new_thoughts is not empty or significantly malformed before assigning
            if not new_thoughts or len(new_thoughts) > len(self.thoughts):
                raise ValueError("Condensing resulted in invalid state.")
            self.thoughts = new_thoughts
        except Exception as e:
            # Consider logging the error here instead of or in addition to raising an exception
            raise RuntimeError(f"Error condensing thoughts: {e}")
