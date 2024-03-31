import traceback

import agenthub.langchains_agent.utils.json as json
import agenthub.langchains_agent.utils.prompts as prompts

class Monologue:
    def __init__(self):
        self.thoughts = []

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

    def condense(self, llm):
        try:
            prompt = prompts.get_summarize_monologue_prompt(self.thoughts)
            messages = [{"content": prompt,"role": "user"}]
            resp = llm.completion(messages=messages)
            summary_resp = resp['choices'][0]['message']['content']
            self.thoughts = prompts.parse_summary_response(strip_markdown(summary_resp))
        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Error condensing thoughts: {e}")

def strip_markdown(markdown_json):
    # remove markdown code block
    return markdown_json.replace('```json\n', '').replace('```', '').strip()