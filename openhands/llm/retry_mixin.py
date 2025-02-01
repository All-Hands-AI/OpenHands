from litellm.exceptions import APIError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from openhands.core.logger import openhands_logger as logger
from openhands.utils.tenacity_stop import stop_if_should_exit


class RetryMixin:
    """Mixin class for retry logic."""

    def retry_decorator(self, **kwargs):
        """
        Create a LLM retry decorator with customizable parameters. This is used for 429 errors, and a few other exceptions in LLM classes.

        Args:
            **kwargs: Keyword arguments to override default retry behavior.
                      Keys: num_retries, retry_exceptions, retry_min_wait, retry_max_wait, retry_multiplier

        Returns:
            A retry decorator with the parameters customizable in configuration.
        """
        num_retries = kwargs.get('num_retries')
        retry_exceptions: tuple = kwargs.get('retry_exceptions', ())
        retry_min_wait = kwargs.get('retry_min_wait')
        retry_max_wait = kwargs.get('retry_max_wait')
        retry_multiplier = kwargs.get('retry_multiplier')
        retry_listener = kwargs.get('retry_listener')

        def before_sleep(retry_state):
            self.log_retry_attempt(retry_state)
            if retry_listener:
                retry_listener(retry_state.attempt_number, num_retries)

        def _filter_exceptions(e):
            # For Cloudflare blocks, don't retry - just return False
            if isinstance(e, APIError) and 'Attention Required! | Cloudflare' in str(e):
                return False

            # Otherwise, return True if we want to retry, which means e is in retry_exceptions
            return isinstance(e, retry_exceptions)

        return retry(
            before_sleep=before_sleep,
            stop=stop_after_attempt(num_retries) | stop_if_should_exit(),
            reraise=True,
            # Use the above filter function to decide whether to retry or not.
            retry=retry_if_exception(_filter_exceptions),
            wait=wait_exponential(
                multiplier=retry_multiplier,
                min=retry_min_wait,
                max=retry_max_wait,
            ),
        )

    def log_retry_attempt(self, retry_state):
        """Log retry attempts."""
        exception = retry_state.outcome.exception()
        logger.error(
            f'{exception}. Attempt #{retry_state.attempt_number} | You can customize retry values in the configuration.',
        )
