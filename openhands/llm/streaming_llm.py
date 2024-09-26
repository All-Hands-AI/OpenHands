import asyncio
from functools import partial

from openhands.core.exceptions import LLMResponseError, UserCancelledError
from openhands.core.logger import openhands_logger as logger
from openhands.llm.async_llm import AsyncLLM


class StreamingLLM(AsyncLLM):
    """Streaming LLM class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._async_streaming_completion = partial(
            self._call_acompletion,
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
            stream=True,  # Ensure streaming is enabled
        )

        async_streaming_completion_unwrapped = self._async_streaming_completion

        @self.retry_decorator(
            num_retries=self.config.num_retries,
            retry_exceptions=self.retry_exceptions,
            retry_min_wait=self.config.retry_min_wait,
            retry_max_wait=self.config.retry_max_wait,
            retry_multiplier=self.config.retry_multiplier,
        )
        async def async_streaming_completion_wrapper(*args, **kwargs):
            # some callers might just send the messages directly
            if 'messages' in kwargs:
                messages = kwargs['messages']
            else:
                messages = args[1] if len(args) > 1 else []

            if not messages:
                raise ValueError(
                    'The messages list is empty. At least one message is required.'
                )

            self.log_prompt(messages)

            try:
                # Directly call and await litellm_acompletion
                resp = await async_streaming_completion_unwrapped(*args, **kwargs)

                # For streaming we iterate over the chunks
                async for chunk in resp:
                    # Check for cancellation before yielding the chunk
                    if (
                        hasattr(self.config, 'on_cancel_requested_fn')
                        and self.config.on_cancel_requested_fn is not None
                        and await self.config.on_cancel_requested_fn()
                    ):
                        raise UserCancelledError(
                            'LLM request cancelled due to CANCELLED state'
                        )
                    # with streaming, it is "delta", not "message"!
                    message_back = chunk['choices'][0]['delta'].get('content', '')
                    if message_back:
                        self.log_response(message_back)
                    self._post_completion(chunk)

                    yield chunk

            except UserCancelledError:
                logger.info('LLM request cancelled by user.')
                raise
            except Exception as e:
                logger.error(f'Completion Error occurred:\n{e}')
                raise

            finally:
                # sleep for 0.1 seconds to allow the stream to be flushed
                if kwargs.get('stream', False):
                    await asyncio.sleep(0.1)

        self._async_streaming_completion = async_streaming_completion_wrapper

    @property
    def async_streaming_completion(self):
        """Decorator for the async litellm acompletion function with streaming."""
        try:
            return self._async_streaming_completion
        except Exception as e:
            raise LLMResponseError(e)
