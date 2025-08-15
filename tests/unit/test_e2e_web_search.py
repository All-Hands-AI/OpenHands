"""Unit tests for the E2E web search test module."""

import pytest


def test_e2e_web_search_module_imports():
    """Test that the E2E web search module can be imported successfully."""
    try:
        # Import the test module to verify it's syntactically correct
        import os
        import sys

        # Add the e2e directory to the path
        e2e_path = os.path.join(os.path.dirname(__file__), '..', 'e2e')
        sys.path.insert(0, e2e_path)

        import test_web_search

        # Verify the test function exists
        assert hasattr(test_web_search, 'test_web_search_current_us_president')
        assert callable(test_web_search.test_web_search_current_us_president)

        # Clean up
        sys.path.remove(e2e_path)

    except ImportError as e:
        pytest.fail(f'Failed to import E2E web search test module: {e}')
    except Exception as e:
        pytest.fail(f'Unexpected error importing E2E web search test module: {e}')


def test_e2e_web_search_test_function_signature():
    """Test that the E2E web search test function has the correct signature."""
    try:
        import inspect
        import os
        import sys

        # Add the e2e directory to the path
        e2e_path = os.path.join(os.path.dirname(__file__), '..', 'e2e')
        sys.path.insert(0, e2e_path)

        import test_web_search

        # Get the function signature
        func = test_web_search.test_web_search_current_us_president
        sig = inspect.signature(func)

        # Verify it takes a 'page' parameter (required for Playwright tests)
        assert 'page' in sig.parameters

        # Verify the parameter has the correct annotation (if present)
        page_param = sig.parameters['page']
        if page_param.annotation != inspect.Parameter.empty:
            # The annotation should be Page from playwright.sync_api
            assert 'Page' in str(page_param.annotation)

        # Clean up
        sys.path.remove(e2e_path)

    except Exception as e:
        pytest.fail(f'Error checking E2E web search test function signature: {e}')
