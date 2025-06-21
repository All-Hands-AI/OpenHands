import asyncio
import copy
import os
import time
import warnings
from functools import partial
from typing import Any, Callable

with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import litellm

from litellm import Message as LiteLLMMessage
from litellm import acompletion as litellm_acompletion
from litellm.types.utils import ModelResponse

from openhands.core.exceptions import LLMNoResponseError, UserCancelledError
from openhands.core.logger import openhands_logger as logger
from openhands.llm.fn_call_converter import (
    STOP_WORDS,
    convert_fncall_messages_to_non_fncall_messages,
    convert_non_fncall_messages_to_fncall_messages,
)
from openhands.llm.llm import (
    LLM,
    LLM_RETRY_EXCEPTIONS,
    MODELS_WITHOUT_STOP_WORDS,
    REASONING_EFFORT_SUPPORTED_MODELS,
)
from openhands.utils.shutdown_listener import should_continue


class AsyncLLM(LLM):
    """Asynchronous LLM class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Set up completion_kwargs for async completion
        completion_kwargs: dict[str, Any] = {
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_output_tokens,
        }

        if self.config.top_k is not None:
            completion_kwargs['top_k'] = self.config.top_k

        if (
            self.config.model.lower() in REASONING_EFFORT_SUPPORTED_MODELS
            or self.config.model.split('/')[-1] in REASONING_EFFORT_SUPPORTED_MODELS
        ):
            completion_kwargs['reasoning_effort'] = self.config.reasoning_effort
            completion_kwargs.pop(
                'temperature'
            )  # temperature is not supported for reasoning models

        # Azure issue: https://github.com/All-Hands-AI/OpenHands/issues/6777
        if self.config.model.startswith('azure'):
            completion_kwargs['max_tokens'] = self.config.max_output_tokens
            completion_kwargs.pop('max_tokens', None)

        self._async_completion = partial(
            self._call_acompletion,
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
            **completion_kwargs,
        )

        async_completion_unwrapped = self._async_completion

        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=LLM_RETRY_EXCEPTIONS,
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
            retry_listener=self.retry_listener,
        )
        async def async_completion_wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for the litellm acompletion function that adds logging and cost tracking."""
            from openhands.io import json

            messages_kwarg: list[dict[str, Any]] | dict[str, Any] = []
            mock_function_calling = not self.is_function_calling_active()

            # some callers might send the model and messages directly
            # litellm allows positional args, like completion(model, messages, **kwargs)
            if len(args) > 1:
                # ignore the first argument if it's provided (it would be the model)
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
                add_in_context_learning_example = True
                if (
                    'openhands-lm' in self.config.model
                    or 'devstral' in self.config.model
                ):
                    add_in_context_learning_example = False

                messages = convert_fncall_messages_to_non_fncall_messages(
                    messages,
                    kwargs['tools'],
                    add_in_context_learning_example=add_in_context_learning_example,
                )
                kwargs['messages'] = messages

                # add stop words if the model supports it
                if self.config.model not in MODELS_WITHOUT_STOP_WORDS:
                    kwargs['stop'] = STOP_WORDS

                mock_fncall_tools = kwargs.pop('tools')
                if 'openhands-lm' in self.config.model:
                    # If we don't have this, we might run into issue when serving openhands-lm
                    # using SGLang
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

            async def check_stopped() -> None:
                while should_continue():
                    if (
                        hasattr(self.config, 'on_cancel_requested_fn')
                        and self.config.on_cancel_requested_fn is not None
                        and await self.config.on_cancel_requested_fn()
                    ):
                        return
                    await asyncio.sleep(0.1)

            stop_check_task = asyncio.create_task(check_stopped())

            try:
                # Record start time for latency measurement
                start_time = time.time()
                # Directly call and await litellm_acompletion
                resp: ModelResponse = await async_completion_unwrapped(*args, **kwargs)

                # Calculate and record latency
                latency = time.time() - start_time
                response_id = resp.get('id', 'unknown')
                self.metrics.add_response_latency(latency, response_id)

                non_fncall_response = copy.deepcopy(resp)

                # if we mocked function calling, and we have tools, convert the response back to function calling format
                if mock_function_calling and mock_fncall_tools is not None:
                    if not resp.get('choices') or len(resp['choices']) < 1:
                        raise LLMNoResponseError(
                            'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                            + str(resp)
                        )

                    non_fncall_response_message = resp['choices'][0]['message']
                    # messages is already a list with proper typing
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
                    resp['choices'][0]['message'] = fn_call_response_message

                # Check if resp has 'choices' key with at least one item
                if not resp.get('choices') or len(resp['choices']) < 1:
                    raise LLMNoResponseError(
                        'Response choices is less than 1 - This is only seen in Gemini models so far. Response: '
                        + str(resp)
                    )

                message_back: str = resp['choices'][0]['message']['content'] or ''
                tool_calls = resp['choices'][0]['message'].get('tool_calls', [])
                if tool_calls:
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict):
                            fn_name = tool_call['function']['name']
                            fn_args = tool_call['function']['arguments']
                        else:
                            fn_name = tool_call.function.name
                            fn_args = tool_call.function.arguments
                        message_back += f'\nFunction call: {fn_name}({fn_args})'

                # log the LLM response
                self.log_response(message_back)

                # post-process the response first to calculate cost
                cost = self._post_completion(resp)

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

                    # if non-native function calling, save messages/response separately
                    if mock_function_calling:
                        # Overwrite response as non-fncall to be consistent with messages
                        _d['response'] = non_fncall_response

                        # Save fncall_messages/response separately
                        _d['fncall_messages'] = original_fncall_messages
                        _d['fncall_response'] = resp
                    with open(log_file, 'w') as f:
                        f.write(json.dumps(_d))

                # We do not support streaming in this method, thus return resp
                return resp

            except UserCancelledError:
                logger.debug('LLM request cancelled by user.')
                raise
            except Exception as e:
                logger.error(f'Completion Error occurred:\n{e}')
                raise

            finally:
                await asyncio.sleep(0.1)
                stop_check_task.cancel()
                try:
                    await stop_check_task
                except asyncio.CancelledError:
                    pass

        self._async_completion = async_completion_wrapper

    async def _call_acompletion(self, *args: Any, **kwargs: Any) -> Any:
        """Wrapper for the litellm acompletion function."""
        # Used in testing?
        return await litellm_acompletion(*args, **kwargs)

    @property
    def async_completion(self) -> Callable:
        """Decorator for the async litellm acompletion function."""
        return self._async_completion
