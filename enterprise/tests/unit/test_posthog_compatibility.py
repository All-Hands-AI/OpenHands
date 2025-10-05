"""Test to ensure PostHog SDK compatibility and identify method availability."""

import posthog
import pytest


def test_posthog_has_identify_attribute():
    """
    Test that posthog module has the 'identify' attribute.
    
    This test will fail if posthog v6.x is installed instead of v4.x,
    as v6.x removed the identify() method in favor of contexts.
    
    Background:
    - The enterprise/server/routes/auth.py calls posthog.identify() at line 177
    - This method exists in posthog v4.x but was removed in v6.x
    - The pyproject.toml specifies posthog = "^4.2.0" which should prevent v6.x
    - However, production logs show: "module 'posthog' has no attribute 'identify'"
    """
    assert hasattr(posthog, 'identify'), (
        "posthog module does not have 'identify' attribute. "
        "This likely means posthog v6.x is installed instead of v4.x. "
        "In v6.x, identify() was removed in favor of the context API. "
        "Check your posthog version: should be ^4.2.0, not 6.x"
    )


def test_posthog_identify_is_callable():
    """
    Test that posthog.identify is a callable function.
    
    This ensures not only that the attribute exists, but that it's actually
    a function that can be called.
    """
    assert hasattr(posthog, 'identify'), "posthog module does not have 'identify' attribute"
    assert callable(posthog.identify), "posthog.identify exists but is not callable"


def test_posthog_identify_with_mock_data():
    """
    Test calling posthog.identify with mock data.
    
    This simulates the actual usage in auth.py without making a real API call.
    The identify method should work even without api_key being set, though it
    will raise an AssertionError about api_key being None.
    """
    # This should not raise AttributeError
    # It may raise AssertionError (api_key must have str, got None) which is expected
    try:
        posthog.identify(
            'test_user_id',
            {
                '$set': {
                    'user_id': 'test_user_id',
                    'test_property': 'test_value',
                }
            },
        )
    except AttributeError as e:
        # This is the actual error we're seeing in production
        pytest.fail(
            f"posthog.identify() raised AttributeError: {e}. "
            "This suggests posthog v6.x is installed where identify() doesn't exist."
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
    Test that posthog version is 4.x, not 6.x.
    
    This test explicitly checks the version to catch any dependency resolution
    issues that might install the wrong version.
    """
    version = posthog.__version__
    major_version = int(version.split('.')[0])
    
    assert major_version == 4, (
        f"Expected posthog version 4.x but got {version}. "
        "The code is written for posthog v4.x API. "
        "Posthog v6.x removed the identify() method."
    )
