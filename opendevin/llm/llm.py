
from litellm import completion as litellm_completion
from litellm import ModelResponse, CustomStreamWrapper
from functools import partial
from typing import Any, cast

from opendevin import config
from opendevin.logging import llm_prompt_logger, llm_response_logger

DEFAULT_API_KEY = cast(str | None, config.get('LLM_API_KEY'))
DEFAULT_BASE_URL = cast(str | None, config.get('LLM_BASE_URL'))
DEFAULT_MODEL_NAME = cast(str, config.get('LLM_MODEL'))
DEFAULT_LLM_NUM_RETRIES = cast(int, config.get('LLM_NUM_RETRIES'))
DEFAULT_LLM_COOLDOWN_TIME = cast(int, config.get('LLM_COOLDOWN_TIME'))


class LLM:
    def __init__(self,
                 model: str = DEFAULT_MODEL_NAME,
                 api_key: str | None = DEFAULT_API_KEY,
                 base_url: str | None = DEFAULT_BASE_URL,
                 num_retries: int = DEFAULT_LLM_NUM_RETRIES,
                 cooldown_time: int = DEFAULT_LLM_COOLDOWN_TIME,
                 ) -> None:
        self.model_name = model if model else DEFAULT_MODEL_NAME
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL

        self._completion = partial(
            litellm_completion, model=self.model_name, api_key=self.api_key, base_url=self.base_url)

        completion_unwrapped = self._completion

        def wrapper(*args: Any, **kwargs: Any) -> ModelResponse | CustomStreamWrapper:
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1]
            llm_prompt_logger.debug(messages)
            resp = completion_unwrapped(*args, **kwargs)
            message_back = resp['choices'][0]['message']['content']
            llm_response_logger.debug(message_back)
            return resp
        self._completion = wrapper  # type: ignore

    @property
    def completion(self) -> partial[ModelResponse | CustomStreamWrapper]:
        """
        Decorator for the litellm completion function.
        """
        return self._completion
