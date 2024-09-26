from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from openhands.core.exceptions import OperationCancelled
from openhands.core.logger import openhands_logger as logger
from openhands.runtime.utils.shutdown_listener import should_exit


class RetryMixin:
    """Mixin class for retry logic."""

    def retry_decorator(self, **kwargs):
        """
        Create a retry decorator with customizable parameters.

        Args:
            **kwargs: Keyword arguments to override default retry behavior.
                      Keys: num_retries, retry_exceptions, retry_min_wait, retry_max_wait, retry_multiplier

        Returns:
            A retry decorator with the specified or default parameters.
        """
        num_retries = kwargs.get('num_retries')
        retry_exceptions = kwargs.get('retry_exceptions')
        retry_min_wait = kwargs.get('retry_min_wait')
        retry_max_wait = kwargs.get('retry_max_wait')
        retry_multiplier = kwargs.get('retry_multiplier')

        def custom_completion_wait(self, retry_state):
            """Custom wait for completion."""
            exception = retry_state.outcome.exception() if retry_state.outcome else None
            if exception is None:
                return 0

            # retry_min_wait = config.retry_min_wait
            # retry_max_wait = config.retry_max_wait

            # rate limit errors
            exception_type = type(exception).__name__
            logger.error(rf'\exception_type: {exception_type}\n')

            if exception_type == 'RateLimitError':
                retry_min_wait = 60
                retry_max_wait = 240
            elif exception_type == 'BadRequestError' and exception.response:
                # this should give us the buried, actual error message
                # from the LLM model.
                logger.error(f'\n\nBadRequestError: {exception.response}\n\n')

            # return the wait time using exponential backoff
            exponential_wait = wait_exponential(
                multiplier=retry_multiplier,
                min=retry_min_wait,
                max=retry_max_wait,
            )

            # call the exponential wait function with retry_state to get the actual wait time
            return exponential_wait(retry_state)

        return retry(
            before_sleep=self.log_retry_attempt,
            stop=stop_after_attempt(num_retries),
            reraise=True,
            retry=(retry_if_exception_type(retry_exceptions)),
            wait=custom_completion_wait,
            # wait=wait_exponential(
            #    multiplier=retry_multiplier,
            #    min=retry_min_wait,
            #    max=retry_max_wait,
            #
        )

    def log_retry_attempt(self, retry_state):
        """Log retry attempts."""
        if should_exit():
            raise OperationCancelled('Operation cancelled.')  # exits the @retry loop
        exception = retry_state.outcome.exception()
        logger.error(
            f'{exception}. Attempt #{retry_state.attempt_number} | You can customize retry values in the configuration.',
            exc_info=False,
        )
