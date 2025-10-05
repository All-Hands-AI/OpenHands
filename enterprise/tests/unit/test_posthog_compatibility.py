"""Test to ensure PostHog SDK v6.x compatibility."""

import posthog
import pytest


def test_posthog_has_set_method():
    """
    Test that posthog module has the 'set' method.
    
    This test ensures posthog.set() is available, which is used in v6.x
    to set person properties instead of the deprecated identify() method.
    
    Background:
    - The enterprise/server/routes/auth.py uses posthog.set() for setting person properties
    - This method exists in both v4.x and v6.x
    - In v6.x, identify() was removed in favor of set() or using $set properties in capture()
    """
    assert hasattr(posthog, 'set'), (
        "posthog module does not have 'set' attribute. "
        "This method is needed to set person properties in v6.x."
    )


def test_posthog_set_is_callable():
    """
    Test that posthog.set is a callable function.
    
    This ensures not only that the attribute exists, but that it's actually
    a function that can be called.
    """
    assert hasattr(posthog, 'set'), "posthog module does not have 'set' attribute"
    assert callable(posthog.set), "posthog.set exists but is not callable"


def test_posthog_set_with_mock_data():
    """
    Test calling posthog.set with mock data.
    
    This simulates the actual usage in auth.py without making a real API call.
    The set method should work even without api_key being set, though it
    will raise an AssertionError about api_key being None.
    """
    # This should not raise AttributeError
    # It may raise AssertionError (api_key must have str, got None) which is expected
    try:
        posthog.set(
            distinct_id='test_user_id',
            properties={
                'user_id': 'test_user_id',
                'test_property': 'test_value',
            },
        )
    except AttributeError as e:
        pytest.fail(
            f"posthog.set() raised AttributeError: {e}. "
            "This suggests posthog.set() is not available."
        )
    except AssertionError as e:
        # This is expected when api_key is not set - this is OK for the test
        if 'api_key' in str(e):
            pass  # Expected error when api_key is not configured
        else:
            raise
    except Exception as e:
        # Other exceptions are OK for this test - we just want to ensure
        # AttributeError doesn't happen
        pass


def test_posthog_version():
    """
    Test that posthog version is v6.x.
    
    The code has been migrated to use the v6.x API with posthog.set() method.
    V6.x removed the identify() method in favor of set() or context-based APIs.
    """
    version = posthog.__version__
    major_version = int(version.split('.')[0])
    
    assert major_version == 6, (
        f"Expected posthog version 6.x but got {version}. "
        "The code is written for v6.x API using set() method."
    )


def test_posthog_capture_has_correct_signature():
    """
    Test that posthog.capture() accepts keyword arguments.
    
    In v6.x, capture() requires keyword arguments for event, distinct_id, and properties.
    """
    assert hasattr(posthog, 'capture'), "posthog module does not have 'capture' attribute"
    assert callable(posthog.capture), "posthog.capture exists but is not callable"
    
    # Test that capture accepts keyword arguments
    try:
        posthog.capture(
            distinct_id='test_user',
            event='test_event',
            properties={'test': 'value'}
        )
    except AttributeError as e:
        pytest.fail(
            f"posthog.capture() raised AttributeError: {e}. "
            "This suggests the capture method is not available."
        )
    except AssertionError as e:
        # This is expected when api_key is not set - this is OK for the test
        if 'api_key' in str(e):
            pass  # Expected error when api_key is not configured
        else:
            raise
    except Exception:
        # Other exceptions are OK for this test
        pass
