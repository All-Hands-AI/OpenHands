import os
import uuid

from litellm import completion as litellm_completion
from functools import partial

from opendevin import config

DEFAULT_MODEL = config.get_or_default("LLM_MODEL", "gpt-4-0125-preview")
DEFAULT_API_KEY = config.get_or_none("LLM_API_KEY")
DEFAULT_BASE_URL = config.get_or_none("LLM_BASE_URL")
PROMPT_DEBUG_DIR = config.get_or_default("PROMPT_DEBUG_DIR", "")

class LLM:
    def __init__(self, model=DEFAULT_MODEL, api_key=DEFAULT_API_KEY, base_url=DEFAULT_BASE_URL, debug_dir=PROMPT_DEBUG_DIR):
        self.model = model if model else DEFAULT_MODEL
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self._debug_dir = debug_dir if debug_dir else PROMPT_DEBUG_DIR
        self._debug_idx = 0
        self._debug_id = uuid.uuid4().hex

        self._completion = partial(litellm_completion, model=self.model, api_key=self.api_key, base_url=self.base_url)

        if self._debug_dir:
            print(f"Logging prompts to {self._debug_dir}/{self._debug_id}")
            completion_unwrapped = self._completion
            def wrapper(*args, **kwargs):
                if "messages" in kwargs:
                    messages = kwargs["messages"]
                else:
                    messages = args[1]
                resp = completion_unwrapped(*args, **kwargs)
                message_back = resp['choices'][0]['message']['content']
                self.write_debug(messages, message_back)
                return resp
            self._completion = wrapper # type: ignore

    @property
    def completion(self):
        """
        Decorator for the litellm completion function.
        """
        return self._completion

    def write_debug(self, messages, response):
        if not self._debug_dir:
            return
        dir = self._debug_dir + "/" + self._debug_id + "/" + str(self._debug_idx)
        os.makedirs(dir, exist_ok=True)
        prompt_out = ""
        for message in messages:
            prompt_out += "<" + message["role"] + ">\n"
            prompt_out += message["content"] + "\n\n"
        with open(f"{dir}/prompt.md", "w") as f:
            f.write(prompt_out)
        with open(f"{dir}/response.md", "w") as f:
            f.write(response)
        self._debug_idx += 1

