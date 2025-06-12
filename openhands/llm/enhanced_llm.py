"""
Enhanced LLM with fallback capabilities.

This module provides an enhanced LLM class that integrates fallback functionality,
automatic error recovery, and DeepSeek R1-0528 as a cost-effective alternative.
"""

import os
from typing import Any, Callable, Optional

from pydantic import SecretStr

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger
from openhands.llm.deepseek_r1 import create_deepseek_r1_llm, is_deepseek_r1_model
from openhands.llm.fallback_manager import (
    FallbackManager,
    create_deepseek_fallback_config,
)
from openhands.llm.llm import LLM
from openhands.llm.metrics import Metrics


class EnhancedLLM:
    """
    Enhanced LLM with automatic fallback capabilities.

    This class wraps the standard LLM class and adds:
    - Automatic fallback to alternative models on failure
    - DeepSeek R1-0528 integration as cost-effective alternative
    - Health monitoring and recovery
    - Performance optimizations
    """

    fallback_manager: Optional['FallbackManager']

    def __init__(
        self,
        config: LLMConfig,
        metrics: Optional[Metrics] = None,
        retry_listener: Optional[Callable[[int, int], None]] = None,
        enable_auto_fallback: bool = True,
    ):
        """
        Initialize the enhanced LLM.

        Args:
            config: Primary LLM configuration
            metrics: Metrics instance for tracking
            retry_listener: Callback for retry events
            enable_auto_fallback: Whether to enable automatic fallback
        """
        self.primary_config = config
        self.metrics = metrics
        self.retry_listener = retry_listener
        self.enable_auto_fallback = enable_auto_fallback

        # Create primary LLM instance
        if is_deepseek_r1_model(config.model):
            self.primary_llm = create_deepseek_r1_llm(
                api_key=config.api_key.get_secret_value() if config.api_key else None,
                base_url=config.base_url,
            )
        else:
            self.primary_llm = LLM(config, metrics, retry_listener)

        # Initialize fallback manager if enabled
        self.fallback_manager = None
        if enable_auto_fallback or config.enable_fallback:
            self._setup_fallback_manager()

    def _setup_fallback_manager(self):
        """Setup the fallback manager with appropriate configurations."""
        fallback_configs = []

        # Add configured fallback models
        if self.primary_config.fallback_models:
            for model_name in self.primary_config.fallback_models:
                fallback_config = self._create_fallback_config(model_name)
                if fallback_config:
                    fallback_configs.append(fallback_config)

        # Add DeepSeek R1-0528 as default fallback if not already included
        deepseek_api_key = self._get_deepseek_api_key()
        if deepseek_api_key and not any(
            'deepseek-r1' in config.model for config in fallback_configs
        ):
            deepseek_config = create_deepseek_fallback_config(deepseek_api_key)
            fallback_configs.append(deepseek_config)

        if fallback_configs:
            self.fallback_manager = FallbackManager(
                self.primary_config, fallback_configs
            )
            logger.info(
                f'Fallback manager initialized with {len(fallback_configs)} fallback models'
            )
        else:
            logger.warning('No fallback configurations available')

    def _create_fallback_config(self, model_name: str) -> Optional[LLMConfig]:
        """Create a fallback configuration for a given model."""
        try:
            # Get API key and base URL for the model
            api_key = self.primary_config.fallback_api_keys.get(model_name)
            base_url = self.primary_config.fallback_base_urls.get(model_name)

            # Use environment variables if not configured
            if not api_key:
                if 'deepseek' in model_name.lower():
                    api_key = os.getenv('DEEPSEEK_API_KEY')
                elif 'openai' in model_name.lower() or 'gpt' in model_name.lower():
                    api_key = os.getenv('OPENAI_API_KEY')
                elif (
                    'anthropic' in model_name.lower() or 'claude' in model_name.lower()
                ):
                    api_key = os.getenv('ANTHROPIC_API_KEY')

            if not api_key:
                logger.warning(f'No API key found for fallback model: {model_name}')
                return None

            # Create fallback configuration
            fallback_config = LLMConfig(
                model=model_name,
                api_key=SecretStr(api_key),
                base_url=base_url,
                temperature=self.primary_config.temperature,
                max_output_tokens=self.primary_config.max_output_tokens,
                timeout=self.primary_config.timeout,
                num_retries=self.primary_config.fallback_max_retries,
            )

            return fallback_config

        except Exception as e:
            logger.error(f'Failed to create fallback config for {model_name}: {e}')
            return None

    def _get_deepseek_api_key(self) -> Optional[str]:
        """Get DeepSeek API key from various sources."""
        # Check configuration
        if 'deepseek-r1-0528' in self.primary_config.fallback_api_keys:
            return self.primary_config.fallback_api_keys['deepseek-r1-0528']

        # Check environment variables
        return os.getenv('DEEPSEEK_API_KEY')

    @property
    def completion(self) -> Callable:
        """Get the completion function with fallback support."""
        if self.fallback_manager and self.enable_auto_fallback:
            return self.fallback_manager.completion
        else:
            return self.primary_llm.completion

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the primary LLM."""
        return getattr(self.primary_llm, name)

    def get_fallback_status(self) -> dict:
        """Get status of fallback providers."""
        if self.fallback_manager:
            return self.fallback_manager.get_provider_status()
        return {}

    def reset_fallback_health(self):
        """Reset health status for all fallback providers."""
        if self.fallback_manager:
            self.fallback_manager.reset_provider_health()

    def is_fallback_enabled(self) -> bool:
        """Check if fallback is enabled and available."""
        return self.fallback_manager is not None and self.enable_auto_fallback


def create_enhanced_llm_with_deepseek_fallback(
    primary_config: LLMConfig, deepseek_api_key: Optional[str] = None, **kwargs
) -> EnhancedLLM:
    """
    Create an enhanced LLM with DeepSeek R1-0528 as fallback.

    Args:
        primary_config: Primary LLM configuration
        deepseek_api_key: DeepSeek API key for fallback
        **kwargs: Additional arguments for EnhancedLLM

    Returns:
        EnhancedLLM instance with DeepSeek fallback
    """
    # Ensure DeepSeek is in fallback models
    if deepseek_api_key:
        if not primary_config.fallback_models:
            primary_config.fallback_models = ['deepseek-r1-0528']
        elif 'deepseek-r1-0528' not in primary_config.fallback_models:
            primary_config.fallback_models.append('deepseek-r1-0528')

        # Add DeepSeek API key to fallback keys
        if not primary_config.fallback_api_keys:
            primary_config.fallback_api_keys = {}
        primary_config.fallback_api_keys['deepseek-r1-0528'] = deepseek_api_key

        # Add DeepSeek base URL
        if not primary_config.fallback_base_urls:
            primary_config.fallback_base_urls = {}
        primary_config.fallback_base_urls['deepseek-r1-0528'] = (
            'https://api.deepseek.com'
        )

        # Enable fallback
        primary_config.enable_fallback = True

    return EnhancedLLM(primary_config, **kwargs)


def get_recommended_fallback_models() -> list[str]:
    """
    Get a list of recommended fallback models in order of preference.

    Returns:
        List of model names for fallback
    """
    return [
        'deepseek-r1-0528',  # Cost-effective and capable
        'gpt-4o-mini',  # Fast and affordable OpenAI model
        'claude-3-5-haiku-20241022',  # Fast Anthropic model
    ]


def auto_configure_fallback(primary_model: str) -> LLMConfig:
    """
    Automatically configure fallback for a primary model.

    Args:
        primary_model: Name of the primary model

    Returns:
        LLMConfig with fallback configured
    """
    config = LLMConfig(model=primary_model)

    # Don't add fallback to itself
    fallback_models = [
        model for model in get_recommended_fallback_models() if model != primary_model
    ]

    config.fallback_models = fallback_models
    config.enable_fallback = True
    config.auto_fallback_on_error = True

    logger.info(f'Auto-configured fallback for {primary_model}: {fallback_models}')

    return config
