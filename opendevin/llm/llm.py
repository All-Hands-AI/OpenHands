from litellm import completion as litellm_completion
from functools import partial
import os

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4-0125-preview")
DEFAULT_API_KEY = os.getenv("LLM_API_KEY")

class LLM:
    def __init__(self, model=DEFAULT_MODEL, api_key=DEFAULT_API_KEY):
        self.model = model if model else DEFAULT_MODEL
        self.api_key = api_key if api_key else DEFAULT_API_KEY

        self._completion = partial(litellm_completion, model=self.model, api_key=self.api_key)


    @property
    def completion(self):
        """
        Decorator for the litellm completion function.
        """
        return self._completion
