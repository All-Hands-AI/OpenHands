from litellm import completion as litellm_completion
from functools import partial
import os

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4-0125-preview")
DEFAULT_API_KEY = os.getenv("LLM_API_KEY")
DEFAULT_BASE_URL = os.getenv("LLM_BASE_URL")

class LLM:
    def __init__(self, model=DEFAULT_MODEL, api_key=DEFAULT_API_KEY, base_url=DEFAULT_BASE_URL):
        self.model = model if model else DEFAULT_MODEL
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL

        self._completion = partial(litellm_completion, model=self.model, api_key=self.api_key, base_url=self.base_url)


    @property
    def completion(self):
        """
        Decorator for the litellm completion function.
        """
        return self._completion
