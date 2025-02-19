from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from openhands.core.logger import openhands_logger as logger
from openhands.utils.tenacity_stop import stop_if_should_exit


class RetryMixin:
    """Mixin class for retry logic."""

    def retry_decorator(
        self,
        *,
        num_retries: int | None = None,
        retry_exceptions: tuple = (),
        retry_min_wait: int | None = None,
        retry_max_wait: int | None = None,
        retry_multiplier: float | None = None,
        retry_listener: Any | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Create a LLM retry decorator with customizable parameters. This is used for 429 errors, and a few other exceptions in LLM classes.

        Args:
            num_retries: Number of retries before giving up
            retry_exceptions: Tuple of exception types to retry on
            retry_min_wait: Minimum wait time between retries in seconds
            retry_max_wait: Maximum wait time between retries in seconds
            retry_multiplier: Multiplier for exponential backoff
            retry_listener: Optional callback for retry events

        Returns:
            A retry decorator with the parameters customizable in configuration.
        """
        num_retries = 3 if num_retries is None else num_retries
        retry_min_wait = 1 if retry_min_wait is None else retry_min_wait
        retry_max_wait = 60 if retry_max_wait is None else retry_max_wait
        retry_multiplier = 2.0 if retry_multiplier is None else retry_multiplier

        def before_sleep(retry_state: Any) -> None:
            self.log_retry_attempt(retry_state)
            if retry_listener:
                retry_listener(retry_state.attempt_number, num_retries)

        return retry(
            before_sleep=before_sleep,
            stop=stop_after_attempt(num_retries) | stop_if_should_exit(),
            reraise=True,
            retry=(
                retry_if_exception_type(retry_exceptions)
            ),  # retry only for these types
            wait=wait_exponential(
                multiplier=retry_multiplier,
                min=retry_min_wait,
                max=retry_max_wait,
            ),
        )

    def log_retry_attempt(self, retry_state: Any) -> None:
        """Log retry attempts."""
        exception = retry_state.outcome.exception()
        logger.error(
            f'{exception}. Attempt #{retry_state.attempt_number} | You can customize retry values in the configuration.',
        )
