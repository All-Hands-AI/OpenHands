from datetime import datetime

from litellm.router import Router
from functools import partial

from opendevin import config
from opendevin.logging import llm_prompt_logger, llm_response_logger

DEFAULT_API_KEY = config.get('LLM_API_KEY')
DEFAULT_BASE_URL = config.get('LLM_BASE_URL')
DEFAULT_MODEL_NAME = config.get('LLM_MODEL')
DEFAULT_LLM_NUM_RETRIES = config.get('LLM_NUM_RETRIES')
DEFAULT_LLM_COOLDOWN_TIME = config.get('LLM_COOLDOWN_TIME')


class LLM:
    def __init__(self,
                 model=DEFAULT_MODEL_NAME,
                 api_key=DEFAULT_API_KEY,
                 base_url=DEFAULT_BASE_URL,
                 num_retries=DEFAULT_LLM_NUM_RETRIES,
                 cooldown_time=DEFAULT_LLM_COOLDOWN_TIME,
                 ):
        self.model_name = model if model else DEFAULT_MODEL_NAME
        self.api_key = api_key if api_key else DEFAULT_API_KEY
        self.base_url = base_url if base_url else DEFAULT_BASE_URL
        self.num_retries = num_retries if num_retries else DEFAULT_LLM_NUM_RETRIES
        self.cooldown_time = cooldown_time if cooldown_time else DEFAULT_LLM_COOLDOWN_TIME
        self._debug_id = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

        # We use litellm's Router in order to support retries (especially rate limit backoff retries).
        # Typically you would use a whole model list, but it's unnecessary with our implementation's structure
        self._router = Router(
            model_list=[{
                'model_name': self.model_name,
                'litellm_params': {
                    'model': self.model_name,
                    'api_key': self.api_key,
                    'api_base': self.base_url
                }
            }],
            num_retries=self.num_retries,
            # We allow all retries to fail, so they can retry instead of going into "cooldown"
            allowed_fails=self.num_retries,
            cooldown_time=self.cooldown_time
        )
        self._completion = partial(
            self._router.completion, model=self.model_name)

        completion_unwrapped = self._completion

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

