from litellm import completion
import os

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4-0125-preview")

class LLM:
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        if self.model == "" or self.model is None:
            self.model = DEFAULT_MODEL

    def prompt_with_messages(self, messages, args: dict={}):
        if self.model == 'fake':
            return "This is a fake response"
        resp = completion(model=self.model, messages=messages, **args)
        return resp['choices'][0]['message']['content']

    def prompt(self, prompt: str, args: dict={}):
        message = [{ "content": prompt,"role": "user"}]
        return self.prompt_with_messages(message, args)
