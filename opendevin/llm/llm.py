
from litellm import completion as litellm_completion
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential
from litellm.exceptions import APIConnectionError, RateLimitError, ServiceUnavailableError
from functools import partial

from opendevin import config
from opendevin.logger import llm_prompt_logger, llm_response_logger, opendevin_logger

DEFAULT_API_KEY = config.get('LLM_API_KEY')
DEFAULT_BASE_URL = config.get('LLM_BASE_URL')
DEFAULT_MODEL_NAME = config.get('LLM_MODEL')
LLM_NUM_RETRIES = config.get('LLM_NUM_RETRIES')
LLM_MIN_WAIT = config.get('MIN_WAIT')
LLM_MAX_WAIT = config.get('MAX_WAIT')


class LLM:
    """
    The LLM class represents a Language Model instance.
    """

    def __init__(self,
                 model=DEFAULT_MODEL_NAME,
                 api_key=DEFAULT_API_KEY,
                 base_url=DEFAULT_BASE_URL,
                 num_retries=LLM_NUM_RETRIES,
                 min_wait=LLM_MIN_WAIT,
                 max_wait=LLM_MAX_WAIT,
                 ):
        """
        Args:
            model (str, optional): The name of the language model. Defaults to LLM_MODEL.
            api_key (str, optional): The API key for accessing the language model. Defaults to LLM_API_KEY.
            base_url (str, optional): The base URL for the language model API. Defaults to LLM_BASE_URL. Not necessary for OpenAI.
            num_retries (int, optional): The number of retries for API calls. Defaults to LLM_NUM_RETRIES.
            cooldown_time (int, optional): The cooldown time between retries in seconds. Defaults to LLM_COOLDOWN_TIME.

        Attributes:
            model_name (str): The name of the language model.
            api_key (str): The API key for accessing the language model.
            base_url (str): The base URL for the language model API.
            completion (function): A decorator for the litellm completion function.
        """
        self.model_name = model if model else DEFAULT_MODEL_NAME
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL

        self._completion = partial(
            litellm_completion, model=self.model_name, api_key=self.api_key, base_url=self.base_url)

        completion_unwrapped = self._completion

        def rate_limited_attempt(retry_state):
            opendevin_logger.info(f'{retry_state.outcome.exception}. Attempt #{retry_state.attempt_number} | You can customize these settings in the configuration.')
            return True

        @retry(reraise=True,
               stop=stop_after_attempt(num_retries),
               wait=wait_random_exponential(min=min_wait, max=max_wait), retry=retry_if_exception_type(RateLimitError, APIConnectionError, ServiceUnavailableError), after=rate_limited_attempt)
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
        return f'LLM(model={self.model_name}, base_url={self.base_url})'
