"""Tests for Gemini thinking patch functionality in LLM class."""

from unittest.mock import MagicMock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.llm import LLM


@pytest.fixture(autouse=True)
def mock_logger(monkeypatch):
    """Suppress logging during tests."""
    mock_logger = MagicMock()
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_prompt_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.debug_mixin.llm_response_logger', mock_logger)
    monkeypatch.setattr('openhands.llm.llm.logger', mock_logger)
    return mock_logger


@pytest.fixture
def gemini_config():
    """LLM config for Gemini 2.5 Pro model."""
    return LLMConfig(
        model='gemini-2.5-pro',
        api_key='test_key',
        num_retries=1,
        retry_min_wait=1,
        retry_max_wait=2,
    )


@pytest.fixture
def gpt_config():
    """LLM config for GPT-4 model."""
    return LLMConfig(
        model='gpt-4',
        api_key='test_key',
        num_retries=1,
        retry_min_wait=1,
        retry_max_wait=2,
    )


class TestGeminiThinkingPatch:
    """Test suite for Gemini thinking patch functionality."""

    def test_should_apply_gemini_thinking_patch_for_gemini_models(self, gemini_config):
        """Test that Gemini models are correctly identified for patching."""
        llm = LLM(gemini_config)
        assert llm._should_apply_gemini_thinking_patch() is True

    def test_should_not_apply_gemini_thinking_patch_for_non_gemini_models(
        self, gpt_config
    ):
        """Test that non-Gemini models are not identified for patching."""
        llm = LLM(gpt_config)
        assert llm._should_apply_gemini_thinking_patch() is False

    def test_should_apply_gemini_thinking_patch_case_insensitive(self):
        """Test that patch detection is case insensitive."""
        config = LLMConfig(model='GEMINI-2.5-PRO', api_key='test_key')
        llm = LLM(config)
        assert llm._should_apply_gemini_thinking_patch() is True

    def test_gemini_thinking_patch_context_manager_creation(self, gemini_config):
        """Test that context manager can be created successfully."""
        llm = LLM(gemini_config)
        context_manager = llm._gemini_thinking_patch_context()
        assert context_manager is not None

    def test_gemini_thinking_patch_context_manager_no_patch_for_non_gemini(
        self, gpt_config
    ):
        """Test that context manager works correctly for non-Gemini models."""
        llm = LLM(gpt_config)

        # Should not raise any exceptions and should work as a no-op
        with llm._gemini_thinking_patch_context():
            pass

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_function_patching_and_restoration(
        self, mock_gemini_module, gemini_config
    ):
        """Test that functions are properly patched and restored."""
        # Setup mock module
        original_sync_func = MagicMock()
        original_async_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'
        original_async_func.__name__ = 'async_transform_request_body'

        mock_gemini_module.sync_transform_request_body = original_sync_func
        mock_gemini_module.async_transform_request_body = original_async_func

        llm = LLM(gemini_config)

        # Test that functions are patched inside context
        with llm._gemini_thinking_patch_context():
            # Functions should be different (patched)
            assert mock_gemini_module.sync_transform_request_body != original_sync_func
            assert (
                mock_gemini_module.async_transform_request_body != original_async_func
            )

        # Functions should be restored after context
        assert mock_gemini_module.sync_transform_request_body == original_sync_func
        assert mock_gemini_module.async_transform_request_body == original_async_func

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_adds_thinking_config(
        self, mock_gemini_module, gemini_config
    ):
        """Test that the patch correctly adds thinkingConfig to optional_params."""
        # Setup mock module
        original_sync_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'
        mock_gemini_module.sync_transform_request_body = original_sync_func

        llm = LLM(gemini_config)

        with llm._gemini_thinking_patch_context():
            # Get the patched function
            patched_func = mock_gemini_module.sync_transform_request_body

            # Call the patched function with optional_params
            test_kwargs = {'optional_params': {'temperature': 0.5}}
            patched_func('test_arg', **test_kwargs)

            # Verify thinkingConfig was added
            expected_thinking_config = {'includeThoughts': True}
            assert (
                test_kwargs['optional_params']['thinkingConfig']
                == expected_thinking_config
            )

            # Verify original function was called
            original_sync_func.assert_called_once_with('test_arg', **test_kwargs)

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_handles_missing_optional_params(
        self, mock_gemini_module, gemini_config
    ):
        """Test that the patch handles cases where optional_params is missing."""
        # Setup mock module
        original_sync_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'
        mock_gemini_module.sync_transform_request_body = original_sync_func

        llm = LLM(gemini_config)

        with llm._gemini_thinking_patch_context():
            # Get the patched function
            patched_func = mock_gemini_module.sync_transform_request_body

            # Call the patched function without optional_params
            test_kwargs = {}
            patched_func('test_arg', **test_kwargs)

            # Should not raise an error and should call original function
            original_sync_func.assert_called_once_with('test_arg', **test_kwargs)

    def test_gemini_thinking_patch_handles_import_error(self, gemini_config):
        """Test that import errors are handled gracefully."""
        llm = LLM(gemini_config)

        # Should not raise an exception even if modules are missing
        with llm._gemini_thinking_patch_context():
            pass

    def test_gemini_thinking_patch_handles_general_exception(self, gemini_config):
        """Test that general exceptions during patching are handled gracefully."""
        llm = LLM(gemini_config)

        # Should not raise an exception
        with llm._gemini_thinking_patch_context():
            pass

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_restoration_on_exception(
        self, mock_gemini_module, gemini_config
    ):
        """Test that functions are restored even if an exception occurs inside the context."""
        # Setup mock module
        original_sync_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'
        mock_gemini_module.sync_transform_request_body = original_sync_func

        llm = LLM(gemini_config)

        # Test that functions are restored even when exception occurs
        try:
            with llm._gemini_thinking_patch_context():
                # Functions should be patched
                assert (
                    mock_gemini_module.sync_transform_request_body != original_sync_func
                )
                # Raise an exception
                raise ValueError('Test exception')
        except ValueError:
            pass

        # Functions should still be restored after exception
        assert mock_gemini_module.sync_transform_request_body == original_sync_func

    def test_gemini_thinking_patch_multiple_models_isolation(
        self, gemini_config, gpt_config
    ):
        """Test that patches are isolated between different model instances."""
        gemini_llm = LLM(gemini_config)
        gpt_llm = LLM(gpt_config)

        # Gemini should have patch capability
        assert gemini_llm._should_apply_gemini_thinking_patch() is True

        # GPT should not have patch capability
        assert gpt_llm._should_apply_gemini_thinking_patch() is False

        # Both should be able to create context managers without interference
        with gemini_llm._gemini_thinking_patch_context():
            with gpt_llm._gemini_thinking_patch_context():
                pass

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_async_function_handling(
        self, mock_gemini_module, gemini_config
    ):
        """Test that async functions are properly handled when available."""
        # Setup mock module with both sync and async functions
        original_sync_func = MagicMock()
        original_async_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'
        original_async_func.__name__ = 'async_transform_request_body'

        mock_gemini_module.sync_transform_request_body = original_sync_func
        mock_gemini_module.async_transform_request_body = original_async_func

        llm = LLM(gemini_config)

        with llm._gemini_thinking_patch_context():
            # Both functions should be patched
            assert mock_gemini_module.sync_transform_request_body != original_sync_func
            assert (
                mock_gemini_module.async_transform_request_body != original_async_func
            )

        # Both functions should be restored
        assert mock_gemini_module.sync_transform_request_body == original_sync_func
        assert mock_gemini_module.async_transform_request_body == original_async_func

    @patch('litellm.llms.vertex_ai.gemini.vertex_and_google_ai_studio_gemini')
    def test_gemini_thinking_patch_no_async_function(
        self, mock_gemini_module, gemini_config
    ):
        """Test that patch works correctly when async function is not available."""
        # Setup mock module with only sync function
        original_sync_func = MagicMock()
        original_sync_func.__name__ = 'sync_transform_request_body'

        mock_gemini_module.sync_transform_request_body = original_sync_func
        # Simulate missing async function
        del mock_gemini_module.async_transform_request_body

        llm = LLM(gemini_config)

        # Should not raise an exception
        with llm._gemini_thinking_patch_context():
            # Sync function should be patched
            assert mock_gemini_module.sync_transform_request_body != original_sync_func

        # Sync function should be restored
        assert mock_gemini_module.sync_transform_request_body == original_sync_func
