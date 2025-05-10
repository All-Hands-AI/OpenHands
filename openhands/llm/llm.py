import copy
import os
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable

import httpx

from openhands.core.config import LLMConfig

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from litellm import ChatCompletionMessageToolCall, ModelInfo, PromptTokensDetails
from litellm import Message as LiteLLMMessage
from litellm import completion as litellm_completion
from litellm import completion_cost as litellm_completion_cost
from litellm.exceptions import (
    RateLimitError,
)
from litellm.types.utils import CostPerToken, ModelResponse, Usage
from litellm.utils import create_pretrained_tokenizer

from openhands.core.exceptions import LLMNoResponseError
from openhands.core.logger import openhands_logger as logger
from openhands.core.message import Message
from openhands.llm.critic import (
    LLMCritic,
    ModelResponseWithCriticScore,
    convert_fncall_messages_and_candidate_responses_for_critic,
)
from openhands.llm.debug_mixin import DebugMixin
from openhands.llm.fn_call_converter import (
    STOP_WORDS,
    convert_fncall_messages_to_non_fncall_messages,
    convert_non_fncall_messages_to_fncall_messages,
)
from openhands.llm.metrics import Metrics
from openhands.llm.retry_mixin import RetryMixin

__all__ = ['LLM']

# tuple of exceptions to retry on
LLM_RETRY_EXCEPTIONS: tuple[type[Exception], ...] = (
    RateLimitError,
    litellm.Timeout,
    litellm.InternalServerError,
    LLMNoResponseError,
)

# cache prompt supporting models
# remove this when we gemini and deepseek are supported
CACHE_PROMPT_SUPPORTED_MODELS = [
    'claude-3-7-sonnet-20250219',
    'claude-sonnet-3-7-latest',
    'claude-3-5-sonnet-20241022',
    'claude-3-5-sonnet-20240620',
    'claude-3-5-haiku-20241022',
    'claude-3-haiku-20240307',
    'claude-3-opus-20240229',
]

# function calling supporting models
FUNCTION_CALLING_SUPPORTED_MODELS = [
    'claude-3-7-sonnet-20250219',
    'claude-sonnet-3-7-latest',
    'claude-3-5-sonnet',
    'claude-3-5-sonnet-20240620',
    'claude-3-5-sonnet-20241022',
    'claude-3.5-haiku',
    'claude-3-5-haiku-20241022',
    'gpt-4o-mini',
    'gpt-4o',
    'o1-2024-12-17',
    'o3-mini-2025-01-31',
    'o3-mini',
    'o3',
    'o3-2025-04-16',
    'o4-mini',
    'o4-mini-2025-04-16',
    'gemini-2.5-pro',
    'gpt-4.1',
]

REASONING_EFFORT_SUPPORTED_MODELS = [
    'o1-2024-12-17',
    'o1',
    'o3',
    'o3-2025-04-16',
    'o3-mini-2025-01-31',
    'o3-mini',
    'o4-mini',
    'o4-mini-2025-04-16',
]

MODELS_WITHOUT_STOP_WORDS = [
    'o1-mini',
    'o1-preview',
    'o1',
    'o1-2024-12-17',
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
        retry_listener: Callable[[int, int], None] | None = None,
    ) -> None:
        """Initializes the LLM. If LLMConfig is passed, its values will be the fallback.

        Passing simple parameters always overrides config.

        Args:
            config: The LLM configuration.
            metrics: The metrics to use.
        """
        self._tried_model_info = False
        self.metrics: Metrics = (
            metrics if metrics is not None else Metrics(model_name=config.model)
        )
        self.cost_metric_supported: bool = True
        self.config: LLMConfig = copy.deepcopy(config)

        self.model_info: ModelInfo | None = None
        self.retry_listener = retry_listener
        if self.config.log_completions:
            if self.config.log_completions_folder is None:
                raise RuntimeError(
                    'log_completions_folder is required when log_completions is enabled'
                )
            os.makedirs(self.config.log_completions_folder, exist_ok=True)

        # Initialize critic if enabled
        self.critic = None
        if self.config.use_critic:
            logger.debug('LLM: critic enabled')
            if self.config.critic_num_candidates > 1:
                assert self.config.temperature != 0.0, (
                    'Critic is not supported with temperature == 0.0'
                )
                if self.config.temperature < 0.5:
                    logger.warning(
                        'LLM: critic is enabled, but the temperature is less than 0.5. This is not recommended as it may lead to degraded results.'
                    )
            else:
                assert self.config.critic_num_candidates == 1
                logger.info(
                    'LLM: critic is enabled, but critic_num_candidates is 1. It will add a critic score to each response.'
                )
            self.critic = LLMCritic(self.config)

        # call init_model_info to initialize config.max_output_tokens
        # which is used in partial function
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.init_model_info()
        if self.vision_is_active():
            logger.debug('LLM: model has vision enabled')
        if self.is_caching_prompt_active():
            logger.debug('LLM: caching prompt enabled')
        if self.is_function_calling_active():
            logger.debug('LLM: model supports function calling')

        # if using a custom tokenizer, make sure it's loaded and accessible in the format expected by litellm
        if self.config.custom_tokenizer is not None:
            self.tokenizer = create_pretrained_tokenizer(self.config.custom_tokenizer)
        else:
            self.tokenizer = None

        # set up the completion function
        kwargs: dict[str, Any] = {
            'temperature': self.config.temperature,
            'max_completion_tokens': self.config.max_output_tokens,
        }
        if (
            self.config.model.lower() in REASONING_EFFORT_SUPPORTED_MODELS
            or self.config.model.split('/')[-1] in REASONING_EFFORT_SUPPORTED_MODELS
        ):
            kwargs['reasoning_effort'] = self.config.reasoning_effort
            kwargs.pop(
                'temperature'
            )  # temperature is not supported for reasoning models
        # Azure issue: https://github.com/All-Hands-AI/OpenHands/issues/6777
        if self.config.model.startswith('azure'):
            kwargs['max_tokens'] = self.config.max_output_tokens
            kwargs.pop('max_completion_tokens')

        self._completion = partial(
            litellm_completion,
            model=self.config.model,
            api_key=self.config.api_key.get_secret_value()
            if self.config.api_key
            else None,
            base_url=self.config.base_url,
            api_version=self.config.api_version,
            custom_llm_provider=self.config.custom_llm_provider,
            timeout=self.config.timeout,
            top_p=self.config.top_p,
            drop_params=self.config.drop_params,
            seed=self.config.seed,
            **kwargs,
        )

        self._completion_unwrapped = self._completion

        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=LLM_RETRY_EXCEPTIONS,
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
            retry_listener=self.retry_listener,
        )
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the litellm completion function. Logs the input and output of the completion function."""
            from openhands.io import json

            messages_kwarg: list[dict[str, Any]] | dict[str, Any] = []
            mock_function_calling = not self.is_function_calling_active()

            # some callers might send the model and messages directly
            # litellm allows positional args, like completion(model, messages, **kwargs)
            if len(args) > 1:
                # ignore the first argument if it's provided (it would be the model)
                # design wise: we don't allow overriding the configured values
                # implementation wise: the partial function set the model as a kwarg already
                # as well as other kwargs
                messages_kwarg = args[1] if len(args) > 1 else args[0]
                kwargs['messages'] = messages_kwarg

                # remove the first args, they're sent in kwargs
                args = args[2:]
            elif 'messages' in kwargs:
                messages_kwarg = kwargs['messages']

            # ensure we work with a list of messages
            messages: list[dict[str, Any]] = (
                messages_kwarg if isinstance(messages_kwarg, list) else [messages_kwarg]
            )

            # handle conversion of to non-function calling messages if needed
            original_fncall_messages = copy.deepcopy(messages)
            mock_fncall_tools = None
            # if the agent or caller has defined tools, and we mock via prompting, convert the messages
            if mock_function_calling and 'tools' in kwargs:
                messages = convert_fncall_messages_to_non_fncall_messages(
                    messages,
                    kwargs['tools'],
                    add_in_context_learning_example=bool(
                        'openhands-lm' not in self.config.model
                    ),
                )
                kwargs['messages'] = messages

                # add stop words if the model supports it
                if self.config.model not in MODELS_WITHOUT_STOP_WORDS:
                    kwargs['stop'] = STOP_WORDS

                mock_fncall_tools = kwargs.pop('tools')
                if 'openhands-lm' in self.config.model:
                    # If we don't have this, we might run into issue when serving openhands-lm
                    # using SGLang
                    # BadRequestError: litellm.BadRequestError: OpenAIException - Error code: 400 - {'object': 'error', 'message': '400', 'type': 'Failed to parse fc related info to json format!', 'param': None, 'code': 400}
                    kwargs['tool_choice'] = 'none'
                else:
                    # tool_choice should not be specified when mocking function calling
                    kwargs.pop('tool_choice', None)

            # if we have no messages, something went very wrong
            if not messages:
                raise ValueError(
                    'The messages list is empty. At least one message is required.'
                )

            # log the entire LLM prompt
            self.log_prompt(messages)

            # set litellm modify_params to the configured value
            # True by default to allow litellm to do transformations like adding a default message, when a message is empty
            # NOTE: this setting is global; unlike drop_params, it cannot be overridden in the litellm completion partial
            litellm.modify_params = self.config.modify_params

            # if we're not using litellm proxy, remove the extra_body
            if 'litellm_proxy' not in self.config.model:
                kwargs.pop('extra_body', None)

            # Record start time for latency measurement
            start_time = time.time()

            llm_responses_for_metrics = []  # track all responses for cost calculation purposes
            critic_metadata = None
            if self.critic is not None:
                resp, critic_metadata = self.handle_critic_scoring(
                    args, kwargs, mock_function_calling
                )
                llm_responses_for_metrics.extend(critic_metadata['responses'])
            else:
                # Standard single response generation
                logger.debug(
                    f'LLM: calling litellm completion with model: {self.config.model}, base_url: {self.config.base_url}, args: {args}, kwargs: {kwargs}'
                )
                resp = self._completion_unwrapped(*args, **kwargs)
                llm_responses_for_metrics.append(resp)

            # Calculate and record latency
            latency = time.time() - start_time
            response_id = resp.get('id', 'unknown')
            self.metrics.add_response_latency(latency, response_id)

            non_fncall_response = copy.deepcopy(resp)

            # if we mocked function calling, and we have tools, convert the response back to function calling format
            if mock_function_calling and mock_fncall_tools is not None:
                if len(resp.choices) < 1:
                    raise LLMNoResponseError(
                        'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                        + str(resp)
                    )

                non_fncall_response_message = resp.choices[0].message
                # messages is already a list with proper typing from line 223
                fn_call_messages_with_response = (
                    convert_non_fncall_messages_to_fncall_messages(
                        messages + [non_fncall_response_message], mock_fncall_tools
                    )
                )
                fn_call_response_message = fn_call_messages_with_response[-1]
                if not isinstance(fn_call_response_message, LiteLLMMessage):
                    fn_call_response_message = LiteLLMMessage(
                        **fn_call_response_message
                    )
                resp.choices[0].message = fn_call_response_message

            # Check if resp has 'choices' key with at least one item
            if not resp.get('choices') or len(resp['choices']) < 1:
                raise LLMNoResponseError(
                    'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                    + str(resp)
                )

            message_back: str = resp['choices'][0]['message']['content'] or ''
            tool_calls: list[ChatCompletionMessageToolCall] = resp['choices'][0][
                'message'
            ].get('tool_calls', [])
            if tool_calls:
                for tool_call in tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = tool_call.function.arguments
                    message_back += f'\nFunction call: {fn_name}({fn_args})'

            # log the LLM response
            self.log_response(message_back)

            # post-process the response first to calculate cost
            cost = self._update_metrics(llm_responses_for_metrics)

            # log for evals or other scripts that need the raw completion
            if self.config.log_completions:
                assert self.config.log_completions_folder is not None
                log_file = os.path.join(
                    self.config.log_completions_folder,
                    # use the metric model name (for draft editor)
                    f'{self.metrics.model_name.replace("/", "__")}-{time.time()}.json',
                )

                # set up the dict to be logged
                _d = {
                    'messages': messages,
                    'response': resp,
                    'args': args,
                    'kwargs': {
                        k: v
                        for k, v in kwargs.items()
                        if k not in ('messages', 'client')
                    },
                    'timestamp': time.time(),
                    'cost': cost,
                }

                # Add critic information if available
                if critic_metadata is not None:
                    _d['critic_results'] = critic_metadata

                # if non-native function calling, save messages/response separately
                if mock_function_calling:
                    # Overwrite response as non-fncall to be consistent with messages
                    _d['response'] = non_fncall_response

                    # Save fncall_messages/response separately
                    _d['fncall_messages'] = original_fncall_messages
                    _d['fncall_response'] = resp
                with open(log_file, 'w') as f:
                    f.write(json.dumps(_d))

            return resp

        self._completion = wrapper

    @property
    def completion(self) -> Callable:
        """Decorator for the litellm completion function.

        Check the complete documentation at https://litellm.vercel.app/docs/completion
        """
        return self._completion

    def init_model_info(self) -> None:
        if self._tried_model_info:
            return
        self._tried_model_info = True
        try:
            if self.config.model.startswith('openrouter'):
                self.model_info = litellm.get_model_info(self.config.model)
        except Exception as e:
            logger.debug(f'Error getting model info: {e}')

        if self.config.model.startswith('litellm_proxy/'):
            # IF we are using LiteLLM proxy, get model info from LiteLLM proxy
            # GET {base_url}/v1/model/info with litellm_model_id as path param
            base_url = self.config.base_url.strip() if self.config.base_url else ''
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'http://' + base_url

            response = httpx.get(
                f'{base_url}/v1/model/info',
                headers={
                    'Authorization': f'Bearer {self.config.api_key.get_secret_value() if self.config.api_key else None}'
                },
            )

            resp_json = response.json()
            if 'data' not in resp_json:
                logger.error(
                    f'Error getting model info from LiteLLM proxy: {resp_json}'
                )
            all_model_info = resp_json.get('data', [])
            current_model_info = next(
                (
                    info
                    for info in all_model_info
                    if info['model_name']
                    == self.config.model.removeprefix('litellm_proxy/')
                ),
                None,
            )
            if current_model_info:
                self.model_info = current_model_info['model_info']
                logger.debug(f'Got model info from litellm proxy: {self.model_info}')

        # Last two attempts to get model info from NAME
        if not self.model_info:
            try:
                self.model_info = litellm.get_model_info(
                    self.config.model.split(':')[0]
                )
            # noinspection PyBroadException
            except Exception:
                pass
        if not self.model_info:
            try:
                self.model_info = litellm.get_model_info(
                    self.config.model.split('/')[-1]
                )
            # noinspection PyBroadException
            except Exception:
                pass
        from openhands.io import json

        logger.debug(f'Model info: {json.dumps(self.model_info, indent=2)}')

        if self.config.model.startswith('huggingface'):
            # HF doesn't support the OpenAI default value for top_p (1)
            logger.debug(
                f'Setting top_p to 0.9 for Hugging Face model: {self.config.model}'
            )
            self.config.top_p = 0.9 if self.config.top_p == 1 else self.config.top_p

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
            if any(
                model in self.config.model
                for model in ['claude-3-7-sonnet', 'claude-3.7-sonnet']
            ):
                self.config.max_output_tokens = 64000  # litellm set max to 128k, but that requires a header to be set

        # Initialize function calling capability
        # Check if model name is in our supported list
        model_name_supported = (
            self.config.model in FUNCTION_CALLING_SUPPORTED_MODELS
            or self.config.model.split('/')[-1] in FUNCTION_CALLING_SUPPORTED_MODELS
            or any(m in self.config.model for m in FUNCTION_CALLING_SUPPORTED_MODELS)
        )

        # Handle native_tool_calling user-defined configuration
        if self.config.native_tool_calling is None:
            self._function_calling_active = model_name_supported
        elif self.config.native_tool_calling is False:
            self._function_calling_active = False
        else:
            # try to enable native tool calling if supported by the model
            self._function_calling_active = litellm.supports_function_calling(
                model=self.config.model
            )

    def vision_is_active(self) -> bool:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return not self.config.disable_vision and self._supports_vision()

    def _supports_vision(self) -> bool:
        """Acquire from litellm if model is vision capable.

        Returns:
            bool: True if model is vision capable. Return False if model not supported by litellm.
        """
        # litellm.supports_vision currently returns False for 'openai/gpt-...' or 'anthropic/claude-...' (with prefixes)
        # but model_info will have the correct value for some reason.
        # we can go with it, but we will need to keep an eye if model_info is correct for Vertex or other providers
        # remove when litellm is updated to fix https://github.com/BerriAI/litellm/issues/5608
        # Check both the full model name and the name after proxy prefix for vision support
        return (
            litellm.supports_vision(self.config.model)
            or litellm.supports_vision(self.config.model.split('/')[-1])
            or (
                self.model_info is not None
                and self.model_info.get('supports_vision', False)
            )
        )

    def is_caching_prompt_active(self) -> bool:
        """Check if prompt caching is supported and enabled for current model.

        Returns:
            boolean: True if prompt caching is supported and enabled for the given model.
        """
        return (
            self.config.caching_prompt is True
            and (
                self.config.model in CACHE_PROMPT_SUPPORTED_MODELS
                or self.config.model.split('/')[-1] in CACHE_PROMPT_SUPPORTED_MODELS
            )
            # We don't need to look-up model_info, because only Anthropic models needs the explicit caching breakpoint
        )

    def is_function_calling_active(self) -> bool:
        """Returns whether function calling is supported and enabled for this LLM instance.

        The result is cached during initialization for performance.
        """
        return self._function_calling_active

    def _update_metrics_for_single_completion(self, response: ModelResponse) -> float:
        """Post-process a single completion response.

        Logs the cost and usage stats of the completion call.
        Returns the cost of the completion.
        """
        try:
            cur_cost = self._completion_cost(response)
        except Exception:
            cur_cost = 0
            # Log the error if cost calculation fails for a single response
            response_id = response.get('id', 'unknown')
            logger.warning(
                f'Could not calculate cost for response_id: {response_id}',
                exc_info=True,
            )

        stats = ''
        if self.cost_metric_supported:
            # keep track of the cost
            stats = 'Cost: %.2f USD | Accumulated Cost: %.2f USD\n' % (
                cur_cost,
                self.metrics.accumulated_cost,
            )

        # Add latency to stats if available
        # Assuming latency is tracked elsewhere and added to metrics before this call
        # If processing a list, latency might need different handling (e.g., average, total)
        # For simplicity, we'll log latency based on the latest entry if available
        if self.metrics.response_latencies:
            latest_latency = self.metrics.response_latencies[-1]
            stats += 'Response Latency: %.3f seconds\n' % latest_latency.latency

        usage: Usage | None = response.get('usage')
        response_id = response.get('id', 'unknown')

        if usage:
            # keep track of the input and output tokens
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)

            if prompt_tokens:
                stats += 'Input tokens: ' + str(prompt_tokens)

            if completion_tokens:
                stats += (
                    (' | ' if prompt_tokens else '')
                    + 'Output tokens: '
                    + str(completion_tokens)
                    + '\n'
                )

            # read the prompt cache hit, if any
            prompt_tokens_details: PromptTokensDetails = usage.get(
                'prompt_tokens_details'
            )
            cache_hit_tokens = (
                prompt_tokens_details.cached_tokens
                if prompt_tokens_details and prompt_tokens_details.cached_tokens
                else 0
            )
            if cache_hit_tokens:
                stats += 'Input tokens (cache hit): ' + str(cache_hit_tokens) + '\n'

            # For Anthropic, the cache writes have a different cost than regular input tokens
            # but litellm doesn't separate them in the usage stats
            # we can read it from the provider-specific extra field
            model_extra = usage.get('model_extra', {})
            cache_write_tokens = model_extra.get('cache_creation_input_tokens', 0)
            if cache_write_tokens:
                stats += 'Input tokens (cache write): ' + str(cache_write_tokens) + '\n'

            # Get context window from model info
            context_window = 0
            if self.model_info and 'max_input_tokens' in self.model_info:
                context_window = self.model_info['max_input_tokens']
                logger.debug(f'Using context window: {context_window}')

            # Record in metrics
            # We'll treat cache_hit_tokens as "cache read" and cache_write_tokens as "cache write"
            self.metrics.add_token_usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cache_read_tokens=cache_hit_tokens,
                cache_write_tokens=cache_write_tokens,
                context_window=context_window,
                response_id=response_id,
            )

        # log the stats for this single response
        if stats:
            logger.debug(f'Stats for response_id {response_id}:\n{stats}')

        return cur_cost

    def _update_metrics(self, llm_responses_for_metrics: list[ModelResponse]) -> float:
        """Post-process the completion response(s).

        Logs the cost and usage stats for single or multiple completion calls.
        Returns the total cost.
        """
        assert len(llm_responses_for_metrics) > 0, 'expected at least one response'
        total_cost = 0.0
        logger.debug(f'Processing {len(llm_responses_for_metrics)} responses.')
        for i, resp in enumerate(llm_responses_for_metrics):
            # Process each response individually
            cost = self._update_metrics_for_single_completion(resp)
            total_cost += cost
            logger.debug(
                f'Processed response {i + 1}/{len(llm_responses_for_metrics)}. Cost: {cost:.4f} USD. Accumulated total: {total_cost:.4f} USD'
            )
        logger.debug(
            f'Finished processing list of {len(llm_responses_for_metrics)} responses. Total cost: {total_cost:.4f} USD.'
        )
        return total_cost

    def get_token_count(self, messages: list[dict] | list[Message]) -> int:
        """Get the number of tokens in a list of messages. Use dicts for better token counting.

        Args:
            messages (list): A list of messages, either as a list of dicts or as a list of Message objects.
        Returns:
            int: The number of tokens.
        """
        # attempt to convert Message objects to dicts, litellm expects dicts
        if (
            isinstance(messages, list)
            and len(messages) > 0
            and isinstance(messages[0], Message)
        ):
            logger.info(
                'Message objects now include serialized tool calls in token counting'
            )
            # Assert the expected type for format_messages_for_llm
            assert isinstance(messages, list) and all(
                isinstance(m, Message) for m in messages
            ), 'Expected list of Message objects'

            # We've already asserted that messages is a list of Message objects
            # Use explicit typing to satisfy mypy
            messages_typed: list[Message] = messages  # type: ignore
            messages = self.format_messages_for_llm(messages_typed)

        # try to get the token count with the default litellm tokenizers
        # or the custom tokenizer if set for this LLM configuration
        try:
            return int(
                litellm.token_counter(
                    model=self.config.model,
                    messages=messages,
                    custom_tokenizer=self.tokenizer,
                )
            )
        except Exception as e:
            # limit logspam in case token count is not supported
            logger.error(
                f'Error getting token count for\n model {self.config.model}\n{e}'
                + (
                    f'\ncustom_tokenizer: {self.config.custom_tokenizer}'
                    if self.config.custom_tokenizer is not None
                    else ''
                )
            )
            return 0

    def _is_local(self) -> bool:
        """Determines if the system is using a locally running LLM.

        Returns:
            boolean: True if executing a local model.
        """
        if self.config.base_url is not None:
            for substring in ['localhost', '127.0.0.1', '0.0.0.0']:
                if substring in self.config.base_url:
                    return True
        elif self.config.model is not None:
            if self.config.model.startswith('ollama'):
                return True
        return False

    def _completion_cost(self, response: Any) -> float:
        """Calculate completion cost and update metrics with running total.

        Calculate the cost of a completion response based on the model. Local models are treated as free.
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
            logger.debug(f'Using custom cost per token: {cost_per_token}')
            extra_kwargs['custom_cost_per_token'] = cost_per_token

        # try directly get response_cost from response
        _hidden_params = getattr(response, '_hidden_params', {})
        cost = _hidden_params.get('additional_headers', {}).get(
            'llm_provider-x-litellm-response-cost', None
        )
        if cost is not None:
            cost = float(cost)
            logger.debug(f'Got response_cost from response: {cost}')

        try:
            if cost is None:
                try:
                    cost = litellm_completion_cost(
                        completion_response=response, **extra_kwargs
                    )
                except Exception as e:
                    logger.debug(f'Error getting cost from litellm: {e}')

            if cost is None:
                _model_name = '/'.join(self.config.model.split('/')[1:])
                cost = litellm_completion_cost(
                    completion_response=response, model=_model_name, **extra_kwargs
                )
                logger.debug(
                    f'Using fallback model name {_model_name} to get cost: {cost}'
                )
            self.metrics.add_cost(float(cost))
            return float(cost)
        except Exception:
            self.cost_metric_supported = False
            logger.debug('Cost calculation not supported for this model.')
        return 0.0

    def __str__(self) -> str:
        if self.config.api_version:
            return f'LLM(model={self.config.model}, api_version={self.config.api_version}, base_url={self.config.base_url})'
        elif self.config.base_url:
            return f'LLM(model={self.config.model}, base_url={self.config.base_url})'
        return f'LLM(model={self.config.model})'

    def __repr__(self) -> str:
        return str(self)

    def reset(self) -> None:
        self.metrics.reset()

    def format_messages_for_llm(self, messages: Message | list[Message]) -> list[dict]:
        if isinstance(messages, Message):
            messages = [messages]

        # set flags to know how to serialize the messages
        for message in messages:
            message.cache_enabled = self.is_caching_prompt_active()
            message.vision_enabled = self.vision_is_active()
            message.function_calling_enabled = self.is_function_calling_active()
            if 'deepseek' in self.config.model:
                message.force_string_serializer = True

        # let pydantic handle the serialization
        return [message.model_dump() for message in messages]

    def _caching_aware_repeated_llm_completion(
        self, n: int, llm_args: Any, llm_kwargs: Any
    ) -> list[ModelResponse]:
        """Call the LLM with the given messages in parallel, respecting caching."""
        ret_responses = []
        assert n > 1, 'Expected at least 2 responses for parallel completion'

        # Make the first request separately to make sure prompt is cached
        _start_time = time.time()
        candidate_resp = self._completion_unwrapped(*llm_args, **llm_kwargs)
        ret_responses.append(candidate_resp)
        logger.debug(
            f'Made 1st request for LLM completion in {time.time() - _start_time} seconds'
        )

        # Make the remaining requests in parallel
        logger.debug(f'Making {n - 1} parallel requests for LLM completions')
        _start_time = time.time()
        with ThreadPoolExecutor(max_workers=n - 1) as executor:
            futures = []
            for _ in range(n - 1):
                # Submit each candidate message list to the executor for scoring
                future = executor.submit(
                    self._completion_unwrapped, *llm_args, **llm_kwargs
                )
                futures.append(future)
            for future in futures:
                # Get the result from the completed future
                ret_responses.append(future.result())
        logger.debug(
            f'Made {n - 1} parallel requests for LLM completions in {time.time() - _start_time} seconds'
        )
        return ret_responses

    def handle_critic_scoring(
        self,
        llm_args: Any,
        llm_kwargs: Any,
        mock_function_calling: bool,
    ) -> tuple[ModelResponseWithCriticScore, dict[str, Any]]:
        """Handle critic scoring."""
        assert self.critic is not None, 'critic is not enabled'
        # Generate multiple candidate responses
        logger.debug(
            f'LLM: generating {self.config.critic_num_candidates} candidate responses for critic evaluation'
        )

        # Add n parameter to generate multiple responses
        critic_kwargs = copy.deepcopy(llm_kwargs)
        critic_kwargs['n'] = self.config.critic_num_candidates

        candidate_responses = []
        candidate_response_messages = []
        # Setting `n` is the most cost-effective way to generate multiple responses
        try:
            resp = self._completion_unwrapped(*llm_args, **critic_kwargs)
            candidate_responses.append(resp)
            for response in resp.choices:
                candidate_response_messages.append(response.message)
        except litellm.UnsupportedParamsError:
            logger.debug(
                'LLM: critic is enabled, but the model does not support n parameter. Fallback to doing single response generation multiple times.'
            )
            _candidate_responses = self._caching_aware_repeated_llm_completion(
                self.config.critic_num_candidates, llm_args, llm_kwargs
            )
            for response in _candidate_responses:
                candidate_responses.append(response)
                assert len(response.choices) == 1, 'Expected 1 choice'
                candidate_response_messages.append(response.choices[0].message)

        assert 'messages' in llm_kwargs and llm_kwargs['messages'] is not None, (
            'expected messages to be provided for critic scoring'
        )
        messages = llm_kwargs['messages']

        # NOTE: We need to convert all these to non-fncall messages for critic scoring IF we are using function calling
        if not mock_function_calling:
            assert 'tools' in llm_kwargs and llm_kwargs['tools'] is not None, (
                'expected tools to be provided for critic scoring with function calling'
            )
            list_of_messages_for_scoring = (
                convert_fncall_messages_and_candidate_responses_for_critic(
                    messages,
                    candidate_response_messages,
                    tools=llm_kwargs['tools'],
                )
            )
        else:
            list_of_messages_for_scoring = [
                copy.deepcopy(messages) + [candidate_response_messages[i]]
                for i in range(len(candidate_response_messages))
            ]
        assert len(list_of_messages_for_scoring) == len(candidate_response_messages), (
            'Expected the same number of messages for scoring as candidate responses'
        )
        # Score the candidate responses
        logger.debug(
            f'LLM critic: scoring {len(list_of_messages_for_scoring)} candidate responses'
        )
        critic_results = self.critic.evaluate_candidates(list_of_messages_for_scoring)

        # Pick the best response
        sorted_critic_results = sorted(
            critic_results, key=lambda x: x[1].last_reward, reverse=True
        )
        logger.debug(
            f'LLM critic first 5 rewards: {[x[1].assistant_rewards[:5] for x in sorted_critic_results]}'
        )
        logger.debug(
            f'LLM critic rewards: {[x[1].last_reward for x in sorted_critic_results]}'
        )
        for i, (response_index, critic_result) in enumerate(sorted_critic_results):
            logger.debug(
                f'LLM critic response {i + 1}; reward: {critic_result.last_reward}'
            )
            logger.debug(
                f'Response content: {candidate_responses[response_index].choices[0].message.content}\n'
            )

        best_response_index, best_response_score = sorted_critic_results[0]
        original_model_response = candidate_responses[
            best_response_index
        ]  # This is a ModelResponse
        resp = ModelResponseWithCriticScore(
            **original_model_response.model_dump(),
            critic_score=best_response_score.last_reward,
        )

        critic_metadata = {
            'critic_results': sorted_critic_results,
            'responses': candidate_responses,
        }

        return resp, critic_metadata
