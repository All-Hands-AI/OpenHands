import pytest

from openhands.llm.retry_mixin import RetryMixin


class TestException(Exception):
    pass


class TestExceptionChild(TestException):
    pass


class TestExceptionExcluded(TestException):
    pass


class TestRetryMixin:
    def test_retry_decorator_with_exclude_exceptions(self):
        mixin = RetryMixin()

        # Create a function that raises different exceptions
        attempt_count = 0

        @mixin.retry_decorator(
            num_retries=3,
            retry_exceptions=(TestException,),
            exclude_exceptions=(TestExceptionExcluded,),
            retry_min_wait=0.1,
            retry_max_wait=0.2,
            retry_multiplier=0.1,
        )
        def test_func(exception_type):
            nonlocal attempt_count
            attempt_count += 1
            raise exception_type()

        # Test that retryable exception is retried
        with pytest.raises(TestException):
            test_func(TestException)
        assert attempt_count == 3  # Should retry 2 times after initial attempt

        # Reset counter
        attempt_count = 0

        # Test that child of retryable exception is retried
        with pytest.raises(TestExceptionChild):
            test_func(TestExceptionChild)
        assert attempt_count == 3  # Should retry 2 times after initial attempt

        # Reset counter
        attempt_count = 0

        # Test that excluded exception is not retried
        with pytest.raises(TestExceptionExcluded):
            test_func(TestExceptionExcluded)
        assert attempt_count == 1  # Should not retry
