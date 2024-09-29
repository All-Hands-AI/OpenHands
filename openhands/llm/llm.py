import copy
import time
import warnings
from functools import partial
from typing import Any

from openhands.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm
from litellm import ModelInfo
from litellm import completion as litellm_completion
from litellm import completion_cost as litellm_completion_cost
from litellm.exceptions import (
    APIConnectionError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)
from litellm.types.utils import CostPerToken, ModelResponse, Usage

from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.core.metrics import Metrics
from openhands.llm.debug_mixin import DebugMixin
from openhands.llm.retry_mixin import RetryMixin

__all__ = ['LLM']

# tuple of exceptions to retry on
LLM_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (
    APIConnectionError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
)

# cache prompt supporting models
# remove this when we gemini and deepseek are supported
CACHE_PROMPT_SUPPORTED_MODELS = [
    'claude-3-5-sonnet-20240620',
    'claude-3-haiku-20240307',
    'claude-3-opus-20240229',
    'anthropic/claude-3-opus-20240229',
    'anthropic/claude-3-haiku-20240307',
    'anthropic/claude-3-5-sonnet-20240620',
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
        self.metrics: Metrics = metrics if metrics is not None else Metrics()
        self.cost_metric_supported: bool = True
        self.config: LLMConfig = copy.deepcopy(config)

        # list of LLM completions (for logging purposes). Each completion is a dict with the following keys:
        # - 'messages': list of messages
        # - 'response': response from the LLM
        self.llm_completions: list[dict[str, Any]] = []

        # litellm actually uses base Exception here for unknown model
        self.model_info: ModelInfo | None = None
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

        if self.vision_is_active():
            logger.debug('LLM: model has vision enabled')
        if self.is_caching_prompt_active():
            logger.debug('LLM: caching prompt enabled')

        # Create config_dict with only compatible keys
        config_dict = self.config.get_litellm_compatible_dict()

        # Handle max_tokens parameter
        if 'max_output_tokens' in config_dict:
            config_dict['max_tokens'] = config_dict.pop('max_output_tokens')

        if self.config.router_models:
            valid_router_args = {
                'model_list',
                'assistants_config',
                'redis_url',
                'redis_host',
                'redis_port',
                'redis_password',
                'cache_responses',
                'cache_kwargs',
                'caching_groups',
                'client_ttl',
                'polling_interval',
                'default_priority',
                'num_retries',
                'timeout',
                'default_litellm_params',
                'default_max_parallel_requests',
                'set_verbose',
                'debug_level',
                'default_fallbacks',
                'fallbacks',
                'context_window_fallbacks',
                'content_policy_fallbacks',
                'model_group_alias',
                'enable_pre_call_checks',
                'enable_tag_filtering',
                'retry_after',
                'retry_policy',
                'model_group_retry_policy',
                'allowed_fails',
                'allowed_fails_policy',
                'cooldown_time',
                'disable_cooldowns',
                'routing_strategy',
                'routing_strategy_args',
                'semaphore',
                'alerting_config',
                'router_general_settings',
            }

            merged_router_options = {**self.config.router_options, **config_dict}

            router_config = {
                key: value
                for key, value in {
                    'model_list': self.config.router_models,
                    'routing_strategy': self.config.router_routing_strategy,
                    'num_retries': self.config.router_num_retries,
                    'cooldown_time': self.config.router_cooldown_time,
                    'allowed_fails': self.config.router_allowed_fails,
                    'cache_responses': self.config.router_cache_responses,
                    'cache_kwargs': self.config.router_cache_kwargs,
                    'set_verbose': self.config.router_options.get('set_verbose', False),
                    'debug_level': self.config.router_options.get('debug_level', 0),
                    **merged_router_options,
                }.items()
                if key in valid_router_args
            }
            self.router = litellm.Router(**router_config)
            completion_func = self._router_completion_with_fallback
        else:
            completion_func = partial(litellm_completion, **config_dict)

        def wrapper(*args, **kwargs):
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            messages: list[dict[str, Any]] | dict[str, Any] = []

            # some callers might send the model and messages directly
            # litellm allows positional args, like completion(model, messages, **kwargs)
            if len(args) > 1:
                # ignore the first argument if it's provided (it would be the model)
                # design wise: we don't allow overriding the configured values
                # implementation wise: the partial function set the model as a kwarg already
                # as well as other kwargs
                messages = args[1] if len(args) > 1 else args[0]
                kwargs['messages'] = messages

                # remove the first args, they're sent in kwargs
                args = args[2:]
            elif 'messages' in kwargs:
                messages = kwargs['messages']

            # ensure we work with a list of messages
            messages = messages if isinstance(messages, list) else [messages]

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

            # Call the completion function (either router.completion or litellm_completion)
            # we don't support streaming here, thus we get a ModelResponse
            resp: ModelResponse = completion_func(*args, **kwargs)

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

            message_back: str = resp['choices'][0]['message']['content']

            # log the LLM response
            self.log_response(message_back)

            # post-process the response
            self._post_completion(resp)

            return resp

        # Apply retry decorator only if not using router
        if not self.config.router_models:
            wrapper = self.retry_decorator(
                num_retries=self.config.num_retries,
                retry_exceptions=LLM_RETRY_EXCEPTIONS,
                retry_min_wait=self.config.retry_min_wait,
                retry_max_wait=self.config.retry_max_wait,
                retry_multiplier=self.config.retry_multiplier,
            )(wrapper)

        self._completion = wrapper

    def _router_completion_with_fallback(self, *args, **kwargs):
        # If 'model' is not in kwargs, add the default model
        # if 'model' not in kwargs:
        #     kwargs['model'] = self.config.model
        try:
            return self.router.completion(*args, **kwargs)
        except Exception as e:
            logger.warning(
                f'Router completion failed: {e}. Falling back to default model.'
            )
            # Use the model from kwargs if available, otherwise use a default model
            fallback_model = kwargs.get('model') or self.config.model
            # Ensure 'model' is in kwargs for litellm_completion
            kwargs['model'] = fallback_model
            return litellm_completion(*args, **kwargs)

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
        # litellm.supports_vision currently returns False for 'openai/gpt-...' or 'anthropic/claude-...' (with prefixes)
        # but model_info will have the correct value for some reason.
        # we can go with it, but we will need to keep an eye if model_info is correct for Vertex or other providers
        # remove when litellm is updated to fix https://github.com/BerriAI/litellm/issues/5608
        return litellm.supports_vision(self.config.model) or (
            self.model_info is not None
            and self.model_info.get('supports_vision', False)
        )

    def is_caching_prompt_active(self) -> bool:
        """Check if prompt caching is supported and enabled for current model.

        Returns:
            boolean: True if prompt caching is supported and enabled for the given model.
        """
        return (
            self.config.caching_prompt is True
            and self.model_info is not None
            and self.model_info.get('supports_prompt_caching', False)
            and self.config.model in CACHE_PROMPT_SUPPORTED_MODELS
        )

    def _post_completion(self, response: ModelResponse) -> None:
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

        usage: Usage | None = response.get('usage')

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
            messages = [messages]

        # set flags to know how to serialize the messages
        for message in messages:
            message.cache_enabled = self.is_caching_prompt_active()
            message.vision_enabled = self.vision_is_active()

        # let pydantic handle the serialization
        return [message.model_dump() for message in messages]
