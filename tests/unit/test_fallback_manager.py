"""
Unit tests for the fallback manager.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openhands.core.config import LLMConfig
from openhands.llm.fallback_manager import (
    FallbackManager,
    ProviderHealth,
    create_deepseek_fallback_config,
    create_fallback_manager_with_deepseek,
)


class TestProviderHealth:
    """Test provider health tracking."""

    def setup_method(self):
        """Setup test fixtures."""
        self.health = ProviderHealth('test-provider')

    def test_initial_state(self):
        """Test initial health state."""
        assert self.health.is_healthy is True
        assert self.health.failure_count == 0
        assert self.health.consecutive_failures == 0

    def test_record_success(self):
        """Test recording successful calls."""
        # First record some failures
        self.health.record_failure()
        self.health.record_failure()

        # Then record success
        self.health.record_success()

        assert self.health.is_healthy is True
        assert self.health.failure_count == 0
        assert self.health.consecutive_failures == 0

    def test_record_failure(self):
        """Test recording failed calls."""
        self.health.record_failure()

        assert self.health.failure_count == 1
        assert self.health.consecutive_failures == 1
        assert self.health.is_healthy is True  # Still healthy after 1 failure

    def test_mark_unhealthy_after_failures(self):
        """Test marking provider as unhealthy after multiple failures."""
        # Record 3 consecutive failures
        for _ in range(3):
            self.health.record_failure()

        assert self.health.is_healthy is False
        assert self.health.consecutive_failures == 3

    def test_should_retry_healthy(self):
        """Test retry logic for healthy provider."""
        assert self.health.should_retry() is True

    def test_should_retry_unhealthy_within_limits(self):
        """Test retry logic for unhealthy provider within limits."""
        # Make provider unhealthy but within max failures
        for _ in range(3):
            self.health.record_failure()

        assert self.health.should_retry(max_failures=5) is False  # No cooldown yet

    def test_should_retry_exceeded_max_failures(self):
        """Test retry logic when max failures exceeded."""
        # Exceed max failures
        for _ in range(6):
            self.health.record_failure()

        assert self.health.should_retry(max_failures=5) is False


class TestFallbackManager:
    """Test fallback manager functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.primary_config = LLMConfig(model='gpt-4o', api_key='primary-key')
        self.fallback_config = LLMConfig(
            model='deepseek-r1-0528', api_key='fallback-key'
        )
        self.manager = FallbackManager(self.primary_config, [self.fallback_config])

    def test_initialization(self):
        """Test fallback manager initialization."""
        assert len(self.manager.provider_health) == 2
        assert 'gpt-4o_default' in self.manager.provider_health
        assert 'deepseek-r1-0528_default' in self.manager.provider_health

    def test_get_provider_key(self):
        """Test provider key generation."""
        key = self.manager._get_provider_key(self.primary_config)
        assert key == 'gpt-4o_default'

        config_with_url = LLMConfig(model='test-model', base_url='https://api.test.com')
        key_with_url = self.manager._get_provider_key(config_with_url)
        assert key_with_url == 'test-model_https://api.test.com'

    def test_get_available_providers(self):
        """Test getting available providers."""
        providers = self.manager.get_available_providers()

        assert len(providers) == 2
        # Primary should be first (lower failure count)
        assert providers[0][0].model == 'gpt-4o'
        assert providers[1][0].model == 'deepseek-r1-0528'

    def test_get_available_providers_with_failures(self):
        """Test provider ordering with failures."""
        # Make primary provider fail
        primary_key = self.manager._get_provider_key(self.primary_config)
        self.manager.provider_health[primary_key].record_failure()
        self.manager.provider_health[primary_key].record_failure()
        self.manager.provider_health[primary_key].record_failure()

        providers = self.manager.get_available_providers()

        # Fallback should now be first (primary is unhealthy)
        assert providers[0][0].model == 'deepseek-r1-0528'

    @patch('openhands.llm.fallback_manager.LLM')
    @pytest.mark.asyncio
    async def test_call_with_fallback_success(self, mock_llm_class):
        """Test successful call with fallback."""
        mock_llm = Mock()
        mock_method = AsyncMock(return_value='success')
        mock_llm.test_method = mock_method
        mock_llm_class.return_value = mock_llm

        result = await self.manager.call_with_fallback(
            'test_method', 'arg1', kwarg1='value1'
        )

        assert result == 'success'
        mock_method.assert_called_once_with('arg1', kwarg1='value1')

    @patch('openhands.llm.fallback_manager.LLM')
    @pytest.mark.asyncio
    async def test_call_with_fallback_primary_fails(self, mock_llm_class):
        """Test fallback when primary fails."""
        # Create two different LLM instances
        primary_llm = Mock()
        fallback_llm = Mock()

        # Primary fails, fallback succeeds
        primary_method = AsyncMock(side_effect=Exception('Primary failed'))
        fallback_method = AsyncMock(return_value='fallback success')

        primary_llm.test_method = primary_method
        fallback_llm.test_method = fallback_method

        # Return different instances based on config
        def llm_side_effect(config):
            if config.model == 'gpt-4o':
                return primary_llm
            else:
                return fallback_llm

        mock_llm_class.side_effect = llm_side_effect

        result = await self.manager.call_with_fallback('test_method', 'arg1')

        assert result == 'fallback success'
        primary_method.assert_called_once()
        fallback_method.assert_called_once()

    @patch('openhands.llm.fallback_manager.LLM')
    @pytest.mark.asyncio
    async def test_call_with_fallback_all_fail(self, mock_llm_class):
        """Test when all providers fail."""
        mock_llm = Mock()
        mock_method = AsyncMock(side_effect=Exception('All failed'))
        mock_llm.test_method = mock_method
        mock_llm_class.return_value = mock_llm

        with pytest.raises(Exception, match='All failed'):
            await self.manager.call_with_fallback('test_method')

    def test_completion_wrapper(self):
        """Test completion wrapper method."""
        with patch.object(self.manager, 'call_with_fallback') as mock_call:
            mock_call.return_value = asyncio.Future()
            mock_call.return_value.set_result('test result')

            # This should work without async/await
            self.manager.completion('test', 'args')

            mock_call.assert_called_once_with('completion', 'test', 'args')

    def test_get_provider_status(self):
        """Test getting provider status."""
        status = self.manager.get_provider_status()

        assert len(status) == 2
        for provider_status in status.values():
            assert 'is_healthy' in provider_status
            assert 'failure_count' in provider_status
            assert 'consecutive_failures' in provider_status

    def test_reset_provider_health(self):
        """Test resetting provider health."""
        # Make a provider unhealthy
        primary_key = self.manager._get_provider_key(self.primary_config)
        for _ in range(3):
            self.manager.provider_health[primary_key].record_failure()

        assert self.manager.provider_health[primary_key].is_healthy is False

        # Reset specific provider
        self.manager.reset_provider_health(primary_key)
        assert self.manager.provider_health[primary_key].is_healthy is True

    def test_reset_all_provider_health(self):
        """Test resetting all provider health."""
        # Make all providers unhealthy
        for health in self.manager.provider_health.values():
            for _ in range(3):
                health.record_failure()

        # Reset all
        self.manager.reset_provider_health()

        for health in self.manager.provider_health.values():
            assert health.is_healthy is True


class TestFallbackManagerUtils:
    """Test utility functions for fallback manager."""

    def test_create_deepseek_fallback_config(self):
        """Test creating DeepSeek fallback configuration."""
        config = create_deepseek_fallback_config('test-api-key')

        assert config.model == 'deepseek-r1-0528'
        assert config.api_key.get_secret_value() == 'test-api-key'
        assert config.base_url == 'https://api.deepseek.com'
        assert config.temperature == 0.0
        assert config.max_output_tokens == 4096

    def test_create_deepseek_fallback_config_no_key(self):
        """Test creating DeepSeek config without API key."""
        config = create_deepseek_fallback_config()

        assert config.model == 'deepseek-r1-0528'
        assert config.api_key is None

    def test_create_fallback_manager_with_deepseek(self):
        """Test creating fallback manager with DeepSeek."""
        primary_config = LLMConfig(model='gpt-4o')
        manager = create_fallback_manager_with_deepseek(primary_config, 'deepseek-key')

        assert len(manager.fallback_configs) == 1
        assert manager.fallback_configs[0].model == 'deepseek-r1-0528'
        assert manager.fallback_configs[0].api_key.get_secret_value() == 'deepseek-key'

    def test_create_fallback_manager_without_deepseek_key(self):
        """Test creating fallback manager without DeepSeek key."""
        primary_config = LLMConfig(model='gpt-4o')
        manager = create_fallback_manager_with_deepseek(primary_config)

        assert len(manager.fallback_configs) == 0


if __name__ == '__main__':
    pytest.main([__file__])
