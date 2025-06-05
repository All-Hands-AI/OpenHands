"""
Fallback Manager for LLM providers.

This module provides intelligent fallback capabilities when primary LLM providers fail.
It supports automatic failover, provider health checking, and cost optimization.
"""

import asyncio
import time
from typing import Any, Optional

from openhands.core.config import LLMConfig
from openhands.core.exceptions import LLMNoResponseError
from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


class ProviderHealth:
    """Tracks the health status of an LLM provider."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_success_time = int(time.time())
        self.is_healthy = True
        self.consecutive_failures = 0

    def record_success(self):
        """Record a successful API call."""
        self.failure_count = 0
        self.consecutive_failures = 0
        self.last_success_time = int(time.time())
        self.is_healthy = True
        logger.debug(f'Provider {self.provider_name} marked as healthy')

    def record_failure(self):
        """Record a failed API call."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_time = int(time.time())

        # Mark as unhealthy after 3 consecutive failures
        if self.consecutive_failures >= 3:
            self.is_healthy = False
            logger.warning(
                f'Provider {self.provider_name} marked as unhealthy after {self.consecutive_failures} failures'
            )

    def should_retry(self, max_failures: int = 5, cooldown_period: int = 300) -> bool:
        """Check if we should retry this provider."""
        if self.is_healthy:
            return True

        # Don't retry if we've exceeded max failures
        if self.failure_count >= max_failures:
            return False

        # Allow retry after cooldown period
        time_since_failure = int(time.time()) - self.last_failure_time
        return time_since_failure > cooldown_period


class FallbackManager:
    """
    Manages fallback logic for LLM providers.

    Provides intelligent failover between multiple LLM configurations,
    with health monitoring and automatic recovery.
    """

    def __init__(
        self,
        primary_config: LLMConfig,
        fallback_configs: Optional[list[LLMConfig]] = None,
    ):
        """
        Initialize the fallback manager.

        Args:
            primary_config: Primary LLM configuration
            fallback_configs: List of fallback LLM configurations
        """
        self.primary_config = primary_config
        self.fallback_configs = fallback_configs or []
        self.provider_health: dict[str, ProviderHealth] = {}
        self._llm_instances: dict[str, LLM] = {}

        # Initialize health tracking for all providers
        all_configs = [primary_config] + self.fallback_configs
        for config in all_configs:
            provider_key = self._get_provider_key(config)
            self.provider_health[provider_key] = ProviderHealth(provider_key)

    def _get_provider_key(self, config: LLMConfig) -> str:
        """Generate a unique key for a provider configuration."""
        return f'{config.model}_{config.base_url or "default"}'

    def _get_llm_instance(self, config: LLMConfig) -> LLM:
        """Get or create an LLM instance for the given configuration."""
        provider_key = self._get_provider_key(config)
        if provider_key not in self._llm_instances:
            self._llm_instances[provider_key] = LLM(config)
        return self._llm_instances[provider_key]

    def get_available_providers(self) -> list[tuple[LLMConfig, ProviderHealth]]:
        """Get list of available providers sorted by preference."""
        all_configs = [self.primary_config] + self.fallback_configs
        available = []

        for config in all_configs:
            provider_key = self._get_provider_key(config)
            health = self.provider_health[provider_key]

            if health.should_retry():
                available.append((config, health))

        # Sort by health status (healthy first) and then by order of preference
        available.sort(key=lambda x: (not x[1].is_healthy, x[1].failure_count))
        return available

    async def call_with_fallback(self, method_name: str, *args, **kwargs) -> Any:
        """
        Call an LLM method with automatic fallback on failure.

        Args:
            method_name: Name of the LLM method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result from the successful LLM call

        Raises:
            Exception: If all providers fail
        """
        available_providers = self.get_available_providers()

        if not available_providers:
            raise LLMNoResponseError('No available LLM providers')

        last_exception = None

        for config, health in available_providers:
            provider_key = self._get_provider_key(config)
            llm_instance = self._get_llm_instance(config)

            try:
                logger.debug(f'Attempting LLM call with provider: {provider_key}')

                # Get the method from the LLM instance
                method = getattr(llm_instance, method_name)

                # Call the method
                if asyncio.iscoroutinefunction(method):
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)

                # Record success
                health.record_success()
                logger.debug(f'LLM call succeeded with provider: {provider_key}')

                return result

            except Exception as e:
                logger.warning(
                    f'LLM call failed with provider {provider_key}: {str(e)}'
                )
                health.record_failure()
                last_exception = e
                continue

        # If we get here, all providers failed
        raise last_exception or LLMNoResponseError('All LLM providers failed')

    def completion(self, *args, **kwargs) -> Any:
        """Wrapper for LLM completion with fallback."""
        return asyncio.run(self.call_with_fallback('completion', *args, **kwargs))

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Get status information for all providers."""
        status = {}
        for provider_key, health in self.provider_health.items():
            status[provider_key] = {
                'is_healthy': health.is_healthy,
                'failure_count': health.failure_count,
                'consecutive_failures': health.consecutive_failures,
                'last_success_time': health.last_success_time,
                'last_failure_time': health.last_failure_time,
            }
        return status

    def reset_provider_health(self, provider_key: Optional[str] = None):
        """Reset health status for a specific provider or all providers."""
        if provider_key:
            if provider_key in self.provider_health:
                self.provider_health[provider_key] = ProviderHealth(provider_key)
        else:
            for key in self.provider_health:
                self.provider_health[key] = ProviderHealth(key)


def create_deepseek_fallback_config(api_key: Optional[str] = None) -> LLMConfig:
    """
    Create a DeepSeek R1-0528 fallback configuration.

    Args:
        api_key: DeepSeek API key (optional)

    Returns:
        LLMConfig configured for DeepSeek R1-0528
    """
    from pydantic import SecretStr

    return LLMConfig(
        model='deepseek-r1-0528',
        api_key=SecretStr(api_key) if api_key else None,
        base_url='https://api.deepseek.com',
        temperature=0.0,
        max_output_tokens=4096,
        timeout=60,
        num_retries=3,
        retry_min_wait=1,
        retry_max_wait=10,
    )


def create_fallback_manager_with_deepseek(
    primary_config: LLMConfig, deepseek_api_key: Optional[str] = None
) -> FallbackManager:
    """
    Create a fallback manager with DeepSeek R1-0528 as fallback.

    Args:
        primary_config: Primary LLM configuration
        deepseek_api_key: DeepSeek API key for fallback

    Returns:
        FallbackManager with DeepSeek fallback configured
    """
    fallback_configs = []

    # Add DeepSeek R1-0528 as fallback if API key is provided
    if deepseek_api_key:
        deepseek_config = create_deepseek_fallback_config(deepseek_api_key)
        fallback_configs.append(deepseek_config)

    return FallbackManager(primary_config, fallback_configs)
