import importlib
import os
import sys
from unittest import mock

import litellm
import pytest


@pytest.fixture
def reset_litellm():
    """Reset litellm settings and logger module after each test."""
    yield
    litellm.suppress_debug_info = False
    litellm.set_verbose = False
    # Remove logger module from sys.modules to force reload
    if 'openhands.core.logger' in sys.modules:
        del sys.modules['openhands.core.logger']


def test_litellm_settings_debug_llm_disabled(reset_litellm):
    """Test that litellm settings are properly configured when DEBUG_LLM is disabled."""
    with mock.patch.dict(os.environ, {'DEBUG_LLM': 'false'}):
        import openhands.core.logger  # noqa: F401

        importlib.reload(openhands.core.logger)

        assert litellm.suppress_debug_info is True
        assert litellm.set_verbose is False


def test_litellm_settings_debug_llm_enabled(reset_litellm):
    """Test that litellm settings are properly configured when DEBUG_LLM is enabled and confirmed."""
    with (
        mock.patch.dict(os.environ, {'DEBUG_LLM': 'true'}),
        mock.patch('builtins.input', return_value='y'),
    ):
        import openhands.core.logger  # noqa: F401

        importlib.reload(openhands.core.logger)

        assert litellm.suppress_debug_info is False
        assert litellm.set_verbose is True


def test_litellm_settings_debug_llm_enabled_but_declined(reset_litellm):
    """Test that litellm settings remain disabled when DEBUG_LLM is enabled but user declines."""
    with (
        mock.patch.dict(os.environ, {'DEBUG_LLM': 'true'}),
        mock.patch('builtins.input', return_value='n'),
    ):
        import openhands.core.logger  # noqa: F401

        importlib.reload(openhands.core.logger)

        assert litellm.suppress_debug_info is True
        assert litellm.set_verbose is False
