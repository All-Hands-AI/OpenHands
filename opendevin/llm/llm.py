from functools import partial

import litellm
from litellm import completion as litellm_completion
from litellm.exceptions import (
    APIConnectionError,
    RateLimitError,
    ServiceUnavailableError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from opendevin.core import config
from opendevin.core.logger import llm_prompt_logger, llm_response_logger
from opendevin.core.logger import opendevin_logger as logger
from opendevin.core.schema import ConfigType

DEFAULT_API_KEY = config.get(ConfigType.LLM_API_KEY)
DEFAULT_BASE_URL = config.get(ConfigType.LLM_BASE_URL)
DEFAULT_MODEL_NAME = config.get(ConfigType.LLM_MODEL)
DEFAULT_API_VERSION = config.get(ConfigType.LLM_API_VERSION)
LLM_NUM_RETRIES = config.get(ConfigType.LLM_NUM_RETRIES)
LLM_RETRY_MIN_WAIT = config.get(ConfigType.LLM_RETRY_MIN_WAIT)
LLM_RETRY_MAX_WAIT = config.get(ConfigType.LLM_RETRY_MAX_WAIT)
LLM_MAX_INPUT_TOKENS = config.get(ConfigType.LLM_MAX_INPUT_TOKENS)
LLM_MAX_OUTPUT_TOKENS = config.get(ConfigType.LLM_MAX_OUTPUT_TOKENS)
LLM_CUSTOM_LLM_PROVIDER = config.get(ConfigType.LLM_CUSTOM_LLM_PROVIDER)
LLM_TIMEOUT = config.get(ConfigType.LLM_TIMEOUT)
LLM_TEMPERATURE = config.get(ConfigType.LLM_TEMPERATURE)
LLM_TOP_P = config.get(ConfigType.LLM_TOP_P)


class LLM:
    """
    The LLM class represents a Language Model instance.
    """

    def __init__(
        self,
        model=DEFAULT_MODEL_NAME,
        api_key=DEFAULT_API_KEY,
        base_url=DEFAULT_BASE_URL,
        api_version=DEFAULT_API_VERSION,
        num_retries=LLM_NUM_RETRIES,
        retry_min_wait=LLM_RETRY_MIN_WAIT,
        retry_max_wait=LLM_RETRY_MAX_WAIT,
        max_input_tokens=LLM_MAX_INPUT_TOKENS,
        max_output_tokens=LLM_MAX_OUTPUT_TOKENS,
        custom_llm_provider=LLM_CUSTOM_LLM_PROVIDER,
        llm_timeout=LLM_TIMEOUT,
        llm_temperature=LLM_TEMPERATURE,
        llm_top_p=LLM_TOP_P,
    ):
        """
        Args:
            model (str, optional): The name of the language model. Defaults to LLM_MODEL.
            api_key (str, optional): The API key for accessing the language model. Defaults to LLM_API_KEY.
            base_url (str, optional): The base URL for the language model API. Defaults to LLM_BASE_URL. Not necessary for OpenAI.
            api_version (str, optional): The version of the API to use. Defaults to LLM_API_VERSION. Not necessary for OpenAI.
            num_retries (int, optional): The number of retries for API calls. Defaults to LLM_NUM_RETRIES.
            retry_min_wait (int, optional): The minimum time to wait between retries in seconds. Defaults to LLM_RETRY_MIN_TIME.
            retry_max_wait (int, optional): The maximum time to wait between retries in seconds. Defaults to LLM_RETRY_MAX_TIME.
            max_input_tokens (int, optional): The maximum number of tokens to send to the LLM per task. Defaults to LLM_MAX_INPUT_TOKENS.
            max_output_tokens (int, optional): The maximum number of tokens to receive from the LLM per task. Defaults to LLM_MAX_OUTPUT_TOKENS.
            custom_llm_provider (str, optional): A custom LLM provider. Defaults to LLM_CUSTOM_LLM_PROVIDER.
            llm_timeout (int, optional): The maximum time to wait for a response in seconds. Defaults to LLM_TIMEOUT.

        Attributes:
            model_name (str): The name of the language model.
            api_key (str): The API key for accessing the language model.
            base_url (str): The base URL for the language model API.
            api_version (str): The version of the API to use.
        """
        logger.info(f'Initializing LLM with model: {model}')
        self.model_name = model
        self.api_key = api_key
        self.base_url = base_url
        self.api_version = api_version
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.llm_timeout = llm_timeout
        self.custom_llm_provider = custom_llm_provider

        # litellm actually uses base Exception here for unknown model
        self.model_info = None
        try:
            self.model_info = litellm.get_model_info(self.model_name)
        # noinspection PyBroadException
        except Exception:
            logger.warning(f'Could not get model info for {self.model_name}')

        if self.max_input_tokens is None:
            if self.model_info is not None and 'max_input_tokens' in self.model_info:
                self.max_input_tokens = self.model_info['max_input_tokens']
            else:
                # Max input tokens for gpt3.5, so this is a safe fallback for any potentially viable model
                self.max_input_tokens = 4096

        if self.max_output_tokens is None:
            if self.model_info is not None and 'max_output_tokens' in self.model_info:
                self.max_output_tokens = self.model_info['max_output_tokens']
            else:
                # Enough tokens for most output actions, and not too many for a bad llm to get carried away responding
                # with thousands of unwanted tokens
                self.max_output_tokens = 1024

        self._completion = partial(
            litellm_completion,
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            api_version=self.api_version,
            custom_llm_provider=custom_llm_provider,
            max_tokens=self.max_output_tokens,
            timeout=self.llm_timeout,
            temperature=llm_temperature,
            top_p=llm_top_p,
        )

        completion_unwrapped = self._completion

        def attempt_on_error(retry_state):
            logger.error(
                f'{retry_state.outcome.exception()}. Attempt #{retry_state.attempt_number} | You can customize these settings in the configuration.',
                exc_info=False,
            )
            return True

        @retry(
            reraise=True,
            stop=stop_after_attempt(num_retries),
            wait=wait_random_exponential(min=retry_min_wait, max=retry_max_wait),
            retry=retry_if_exception_type(
                (RateLimitError, APIConnectionError, ServiceUnavailableError)
            ),
            after=attempt_on_error,
        )
        def wrapper(*args, **kwargs):
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1]
            debug_message = ''
            for message in messages:
                debug_message += '\n\n----------\n\n' + message['content']
            llm_prompt_logger.debug(debug_message)
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

    def get_token_count(self, messages):
        """
        Get the number of tokens in a list of messages.

        Args:
            messages (list): A list of messages.

        Returns:
            int: The number of tokens.
        """
        return litellm.token_counter(model=self.model_name, messages=messages)

    def __str__(self):
        if self.api_version:
            return f'LLM(model={self.model_name}, api_version={self.api_version}, base_url={self.base_url})'
        elif self.base_url:
            return f'LLM(model={self.model_name}, base_url={self.base_url})'
        return f'LLM(model={self.model_name})'
