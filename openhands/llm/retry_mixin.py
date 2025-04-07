import json
import re
from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from openhands.core.exceptions import LLMNoResponseError
from openhands.core.logger import openhands_logger as logger
from openhands.utils.tenacity_stop import stop_if_should_exit


class RetryMixin:
    """Mixin class for retry logic."""

    def _extract_retry_delay(self, exception) -> float | None:
        """
        Extract retry delay in seconds from exception message if available.

        Args:
            exception: The exception object to extract retry delay from

        Returns:
            Retry delay in seconds or None if not found
        """
        if not hasattr(exception, '__str__'):
            return None

        error_msg = str(exception)

        # Try to extract "retryDelay": "Xs" pattern
        retry_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_msg)
        if retry_match:
            return float(retry_match.group(1))

        # Try to extract any JSON containing retryDelay
        try:
            # Look for JSON objects in the string
            json_match = re.search(r'({.*})', error_msg)
            if json_match:
                json_data = json.loads(json_match.group(1))

                # Navigate through nested JSON to find retryDelay
                if 'error' in json_data and 'details' in json_data['error']:
                    for detail in json_data['error']['details']:
                        if (
                            '@type' in detail
                            and 'RetryInfo' in detail['@type']
                            and 'retryDelay' in detail
                        ):
                            delay_str = detail['retryDelay']
                            if isinstance(delay_str, str) and delay_str.endswith('s'):
                                return float(
                                    delay_str[:-1]
                                )  # Remove the 's' and convert to float
        except Exception:
            # If JSON parsing fails, continue with default retry behavior
            pass

        return None

    def custom_wait_strategy(self, retry_state) -> float:
        """
        Custom wait strategy that uses provider's retry delay when available.

        Args:
            retry_state: The current retry state

        Returns:
            Wait time in seconds
        """
        # Get the fallback exponential wait
        default_wait = wait_exponential(
            multiplier=self.retry_multiplier,
            min=self.retry_min_wait,
            max=self.retry_max_wait,
        )(retry_state)

        # Check if there's an exception with retry delay info
        if retry_state.outcome.failed:
            exception = retry_state.outcome.exception()
            retry_delay = self._extract_retry_delay(exception)

            if retry_delay is not None:
                logger.info(f'Using provider-suggested retry delay: {retry_delay}s')
                return retry_delay

        return default_wait

    def retry_decorator(self, **kwargs: Any) -> Callable:
        """
        Create a LLM retry decorator with customizable parameters. This is used for 429 errors, and a few other exceptions in LLM classes.

        Args:
            **kwargs: Keyword arguments to override default retry behavior.
                      Keys: num_retries, retry_exceptions, retry_min_wait, retry_max_wait, retry_multiplier

        Returns:
            A retry decorator with the parameters customizable in configuration.
        """
        # Store these values as instance variables so they can be accessed by custom_wait_strategy
        self.num_retries = kwargs.get('num_retries')
        self.retry_exceptions = kwargs.get('retry_exceptions', ())
        self.retry_min_wait = kwargs.get('retry_min_wait')
        self.retry_max_wait = kwargs.get('retry_max_wait')
        self.retry_multiplier = kwargs.get('retry_multiplier')
        retry_listener = kwargs.get('retry_listener')

        def before_sleep(retry_state: Any) -> None:
            self.log_retry_attempt(retry_state)
            if retry_listener:
                retry_listener(retry_state.attempt_number, self.num_retries)

            # Check if the exception is LLMNoResponseError
            exception = retry_state.outcome.exception()
            if isinstance(exception, LLMNoResponseError):
                if hasattr(retry_state, 'kwargs'):
                    # Only change temperature if it's zero or not set
                    current_temp = retry_state.kwargs.get('temperature', 0)
                    if current_temp == 0:
                        retry_state.kwargs['temperature'] = 1.0
                        logger.warning(
                            'LLMNoResponseError detected with temperature=0, setting temperature to 1.0 for next attempt.'
                        )
                    else:
                        logger.warning(
                            f'LLMNoResponseError detected with temperature={current_temp}, keeping original temperature'
                        )

        retry_decorator: Callable = retry(
            before_sleep=before_sleep,
            stop=stop_after_attempt(self.num_retries) | stop_if_should_exit(),
            reraise=True,
            retry=retry_if_exception_type(self.retry_exceptions),
            wait=self.custom_wait_strategy,
        )
        return retry_decorator

    def log_retry_attempt(self, retry_state: Any) -> None:
        """Log retry attempts."""
        exception = retry_state.outcome.exception()
        logger.error(
            f'{exception}. Attempt #{retry_state.attempt_number} | You can customize retry values in the configuration.',
        )
