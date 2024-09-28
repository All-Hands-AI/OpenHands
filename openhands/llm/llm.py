import copy
import os
import time
import warnings
from functools import partial
from typing import Any

from openhands.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from litellm import completion as litellm_completion
from litellm import completion_cost as litellm_completion_cost
from litellm.exceptions import (
    APIConnectionError,
    ContentPolicyViolationError,
    InternalServerError,
    OpenAIError,
    RateLimitError,
)
from litellm.types.utils import CostPerToken

from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.core.metrics import Metrics
from openhands.llm.debug_mixin import DebugMixin
from openhands.llm.retry_mixin import RetryMixin

__all__ = ['LLM']

cache_prompting_supported_models = [
    'claude-3-5-sonnet-20240620',
    'claude-3-haiku-20240307',
]


class LLM(RetryMixin, DebugMixin):
    """The LLM class represents a Language Model instance.

    Attributes:
        config: an LLMConfig object specifying the configuration of the LLM.
    """

    def __init__(
        self,
        config: LLMConfig,
        metrics: Metrics | None = None,
    ):
        """Initializes the LLM. If LLMConfig is passed, its values will be the fallback.

        Passing simple parameters always overrides config.

        Args:
            config: The LLM configuration.
            metrics: The metrics to use.
        """
        self.metrics = metrics if metrics is not None else Metrics()
        self.cost_metric_supported = True
        self.config = copy.deepcopy(config)

        os.environ['OR_SITE_URL'] = self.config.openrouter_site_url
        os.environ['OR_APP_NAME'] = self.config.openrouter_app_name

        # list of LLM completions (for logging purposes). Each completion is a dict with the following keys:
        # - 'messages': list of messages
        # - 'response': response from the LLM
        self.llm_completions: list[dict[str, Any]] = []

        # Set up config attributes with default values to prevent AttributeError
        LLMConfig.set_missing_attributes(self.config)

        # litellm actually uses base Exception here for unknown model
        self.model_info = None
        try:
            if self.config.model.startswith('openrouter'):
                self.model_info = litellm.get_model_info(self.config.model)
            else:
                self.model_info = litellm.get_model_info(
                    self.config.model.split(':')[0]
                )
        # noinspection PyBroadException
        except Exception as e:
            logger.warning(f'Could not get model info for {config.model}:\n{e}')

        # Tuple of exceptions to retry on
        self.retry_exceptions = (
            APIConnectionError,
            ContentPolicyViolationError,
            InternalServerError,
            OpenAIError,
            RateLimitError,
        )

        # Set the max tokens in an LM-specific way if not set
        if self.config.max_input_tokens is None:
            if (
                self.model_info is not None
                and 'max_input_tokens' in self.model_info
                and isinstance(self.model_info['max_input_tokens'], int)
            ):
                self.config.max_input_tokens = self.model_info['max_input_tokens']
            else:
                # Safe fallback for any potentially viable model
                self.config.max_input_tokens = 4096

        if self.config.max_output_tokens is None:
            # Safe default for any potentially viable model
            self.config.max_output_tokens = 4096
            if self.model_info is not None:
                # max_output_tokens has precedence over max_tokens, if either exists.
                # litellm has models with both, one or none of these 2 parameters!
                if 'max_output_tokens' in self.model_info and isinstance(
                    self.model_info['max_output_tokens'], int
                ):
                    self.config.max_output_tokens = self.model_info['max_output_tokens']
                elif 'max_tokens' in self.model_info and isinstance(
                    self.model_info['max_tokens'], int
                ):
                    self.config.max_output_tokens = self.model_info['max_tokens']

        self._completion = partial(
            litellm_completion,
            model=self.config.model,
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            max_tokens=self.config.max_output_tokens,
            timeout=self.config.timeout,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            drop_params=self.config.drop_params,
        )

        if self.vision_is_active():
            logger.debug('LLM: model has vision enabled')

        completion_unwrapped = self._completion

        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=self.retry_exceptions,
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
        )
        def wrapper(*args, **kwargs):
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            # some callers might just send the messages directly
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1] if len(args) > 1 else []

            # if we have no messages, something went very wrong
            if not messages:
                raise ValueError(
                    'The messages list is empty. At least one message is required.'
                )

            # log the entire LLM prompt
            self.log_prompt(messages)

            if self.is_caching_prompt_active():
                # Anthropic-specific prompt caching
                if 'claude-3' in self.config.model:
                    kwargs['extra_headers'] = {
                        'anthropic-beta': 'prompt-caching-2024-07-31',
                    }

            resp = completion_unwrapped(*args, **kwargs)

            # log for evals or other scripts that need the raw completion
            if self.config.log_completions:
                self.llm_completions.append(
                    {
                        'messages': messages,
                        'response': resp,
                        'timestamp': time.time(),
                        'cost': self._completion_cost(resp),
                    }
                )

            message_back = resp['choices'][0]['message']['content']

            # log the LLM response
            self.log_response(message_back)

            # post-process the response
            self._post_completion(resp)

            return resp

        self._completion = wrapper

    @property
    def completion(self):
        """Decorator for the litellm completion function.

        Check the complete documentation at https://litellm.vercel.app/docs/completion
        """
        return self._completion

    def vision_is_active(self):
        return not self.config.disable_vision and self._supports_vision()

    def _supports_vision(self):
        """Acquire from litellm if model is vision capable.

        Returns:
            bool: True if model is vision capable. If model is not supported by litellm, it will return False.
        """
        try:
            return litellm.supports_vision(self.config.model)
        except Exception:
            return False

    def is_caching_prompt_active(self) -> bool:
        """Check if prompt caching is enabled and supported for current model.

        Returns:
            boolean: True if prompt caching is active for the given model.
        """
        return self.config.caching_prompt is True and any(
            model in self.config.model for model in cache_prompting_supported_models
        )

    def _post_completion(self, response) -> None:
        """Post-process the completion response.

        Logs the cost and usage stats of the completion call.
        """
        try:
            cur_cost = self._completion_cost(response)
        except Exception:
            cur_cost = 0

        stats = ''
        if self.cost_metric_supported:
            # keep track of the cost
            stats = 'Cost: %.2f USD | Accumulated Cost: %.2f USD\n' % (
                cur_cost,
                self.metrics.accumulated_cost,
            )

        usage = response.get('usage')

        if usage:
            # keep track of the input and output tokens
            input_tokens = usage.get('prompt_tokens')
            output_tokens = usage.get('completion_tokens')

            if input_tokens:
                stats += 'Input tokens: ' + str(input_tokens)

            if output_tokens:
                stats += (
                    (' | ' if input_tokens else '')
                    + 'Output tokens: '
                    + str(output_tokens)
                    + '\n'
                )

            # read the prompt caching status as received from the provider
            model_extra = usage.get('model_extra', {})

            cache_creation_input_tokens = model_extra.get('cache_creation_input_tokens')
            if cache_creation_input_tokens:
                stats += (
                    'Input tokens (cache write): '
                    + str(cache_creation_input_tokens)
                    + '\n'
                )

            cache_read_input_tokens = model_extra.get('cache_read_input_tokens')
            if cache_read_input_tokens:
                stats += (
                    'Input tokens (cache read): ' + str(cache_read_input_tokens) + '\n'
                )

        # log the stats
        if stats:
            logger.info(stats)

    def get_token_count(self, messages):
        """Get the number of tokens in a list of messages.

        Args:
            messages (list): A list of messages.

        Returns:
            int: The number of tokens.
        """
        try:
            return litellm.token_counter(model=self.config.model, messages=messages)
        except Exception:
            # TODO: this is to limit logspam in case token count is not supported
            return 0

    def _is_local(self):
        """Determines if the system is using a locally running LLM.

        Returns:
            boolean: True if executing a local model.
        """
        if self.config.base_url is not None:
            for substring in ['localhost', '127.0.0.1' '0.0.0.0']:
                if substring in self.config.base_url:
                    return True
        elif self.config.model is not None:
            if self.config.model.startswith('ollama'):
                return True
        return False

    def _completion_cost(self, response):
        """Calculate the cost of a completion response based on the model.  Local models are treated as free.
        Add the current cost into total cost in metrics.

        Args:
            response: A response from a model invocation.

        Returns:
            number: The cost of the response.
        """
        if not self.cost_metric_supported:
            return 0.0

        extra_kwargs = {}
        if (
            self.config.input_cost_per_token is not None
            and self.config.output_cost_per_token is not None
        ):
            cost_per_token = CostPerToken(
                input_cost_per_token=self.config.input_cost_per_token,
                output_cost_per_token=self.config.output_cost_per_token,
            )
            logger.info(f'Using custom cost per token: {cost_per_token}')
            extra_kwargs['custom_cost_per_token'] = cost_per_token

        if not self._is_local():
            try:
                cost = litellm_completion_cost(
                    completion_response=response, **extra_kwargs
                )
                self.metrics.add_cost(cost)
                return cost
            except Exception:
                self.cost_metric_supported = False
                logger.warning('Cost calculation not supported for this model.')
        return 0.0

    def __str__(self):
        if self.config.api_version:
            return f'LLM(model={self.config.model}, api_version={self.config.api_version}, base_url={self.config.base_url})'
        elif self.config.base_url:
            return f'LLM(model={self.config.model}, base_url={self.config.base_url})'
        return f'LLM(model={self.config.model})'

    def __repr__(self):
        return str(self)

    def reset(self):
        self.metrics = Metrics()
        self.llm_completions = []

    def format_messages_for_llm(self, messages: Message | list[Message]) -> list[dict]:
        if isinstance(messages, Message):
            return [messages.model_dump()]
        return [message.model_dump() for message in messages]
