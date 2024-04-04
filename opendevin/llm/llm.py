import os
import uuid

from litellm.router import Router
from functools import partial

from opendevin import config

DEFAULT_API_KEY = config.get("LLM_API_KEY")
DEFAULT_BASE_URL = config.get("LLM_BASE_URL")
DEFAULT_MODEL_NAME = config.get("LLM_MODEL")
DEFAULT_LLM_NUM_RETRIES = config.get("LLM_NUM_RETRIES")
DEFAULT_LLM_COOLDOWN_TIME = config.get("LLM_COOLDOWN_TIME")
PROMPT_DEBUG_DIR = config.get("PROMPT_DEBUG_DIR")

class LLM:
    def __init__(self,
            model=DEFAULT_MODEL_NAME,
            api_key=DEFAULT_API_KEY,
            base_url=DEFAULT_BASE_URL,
            num_retries=DEFAULT_LLM_NUM_RETRIES,
            cooldown_time=DEFAULT_LLM_COOLDOWN_TIME,
            debug_dir=PROMPT_DEBUG_DIR
    ):
        self.model_name = model if model else DEFAULT_MODEL_NAME
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self.num_retries = num_retries if num_retries else DEFAULT_LLM_NUM_RETRIES
        self.cooldown_time = cooldown_time if cooldown_time else DEFAULT_LLM_COOLDOWN_TIME
        self._debug_dir = debug_dir if debug_dir else PROMPT_DEBUG_DIR
        self._debug_idx = 0
        self._debug_id = uuid.uuid4().hex

        # We use litellm's Router in order to support retries (especially rate limit backoff retries). 
        # Typically you would use a whole model list, but it's unnecessary with our implementation's structure
        self._router = Router(
            model_list=[{
                "model_name": self.model_name,
                "litellm_params": {
                    "model": self.model_name,
                    "api_key": self.api_key,
                    "api_base": self.base_url
                }
            }],
            num_retries=self.num_retries,
            allowed_fails=self.num_retries, # We allow all retries to fail, so they can retry instead of going into "cooldown"
            cooldown_time=self.cooldown_time,
            # set_verbose=True,
            # debug_level="DEBUG"
        )
        self._completion = partial(self._router.completion, model=self.model_name)

        if self._debug_dir:
            print(f"Logging prompts to {self._debug_dir}/{self._debug_id}")
            completion_unwrapped = self._completion
            def wrapper(*args, **kwargs):
                dir = self._debug_dir + "/" + self._debug_id + "/" + str(self._debug_idx)
                os.makedirs(dir, exist_ok=True)
                if "messages" in kwargs:
                    messages = kwargs["messages"]
                else:
                    messages = args[1]
                self.write_debug_prompt(dir, messages)
                resp = completion_unwrapped(*args, **kwargs)
                message_back = resp['choices'][0]['message']['content']
                self.write_debug_response(dir, message_back)
                self._debug_idx += 1
                return resp
            self._completion = wrapper # type: ignore

    @property
    def completion(self):
        """
        Decorator for the litellm completion function.
        """
        return self._completion

    def write_debug_prompt(self, dir, messages):
        prompt_out = ""
        for message in messages:
            prompt_out += "<" + message["role"] + ">\n"
            prompt_out += message["content"] + "\n\n"
        with open(f"{dir}/prompt.md", "w") as f:
            f.write(prompt_out)

    def write_debug_response(self, dir, response):
        with open(f"{dir}/response.md", "w") as f:
            f.write(response)
