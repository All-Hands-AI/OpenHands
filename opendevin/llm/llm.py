
from litellm import completion as litellm_completion
from tenacity import retry, retry_if_exception_type, stop_after_attempt
from litellm.exceptions import APIConnectionError, RateLimitError
from functools import partial

from opendevin import config
from opendevin.logger import llm_prompt_logger, llm_response_logger, opendevin_logger

DEFAULT_API_KEY = config.get('LLM_API_KEY')
DEFAULT_BASE_URL = config.get('LLM_BASE_URL')
DEFAULT_MODEL_NAME = config.get('LLM_MODEL')
DEFAULT_LLM_NUM_RETRIES = config.get('LLM_NUM_RETRIES')
DEFAULT_LLM_COOLDOWN_TIME = config.get('LLM_COOLDOWN_TIME')
DEFAULT_API_VERSION = config.get('LLM_API_VERSION')


class LLM:
    def __init__(self,
                 model=DEFAULT_MODEL_NAME,
                 api_key=DEFAULT_API_KEY,
                 base_url=DEFAULT_BASE_URL,
                 num_retries=DEFAULT_LLM_NUM_RETRIES,
                 cooldown_time=DEFAULT_LLM_COOLDOWN_TIME,
                 api_version=DEFAULT_API_VERSION,
                 ):
        opendevin_logger.info(f'Initializing LLM with model: {model}')
        self.model_name = model
        self.api_key = api_key
        self.base_url = base_url
        self.api_version = api_version

        self._completion = partial(
            litellm_completion, model=self.model_name, api_key=self.api_key, base_url=self.base_url, api_version=self.api_version)

        completion_unwrapped = self._completion

        def my_wait(retry_state):
            seconds = (retry_state.attempt_number) * cooldown_time
            opendevin_logger.warning(f'LLM error: {retry_state.outcome.exception()}')
            opendevin_logger.info(f'Attempt #{retry_state.attempt_number} | Sleeping for {seconds}s')
            return seconds

        @retry(reraise=True,
               stop=stop_after_attempt(num_retries),
               wait=my_wait, retry=retry_if_exception_type((APIConnectionError, RateLimitError)))
        def wrapper(*args, **kwargs):
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
    def completion(self):
        """
        Decorator for the litellm completion function.
        """
        return self._completion

    def __str__(self):
        if self.api_version:
            return f'LLM(model={self.model_name}, api_version={self.api_version}, base_url={self.base_url})'
        elif self.base_url:
            return f'LLM(model={self.model_name}, base_url={self.base_url})'
        return f'LLM(model={self.model_name})'
