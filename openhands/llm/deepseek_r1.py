"""
DeepSeek R1 specific optimizations and configurations.

This module provides specialized handling for DeepSeek R1 models,
including performance optimizations and model-specific configurations.
"""

import os
from typing import Any, Optional

from openhands.core.config import LLMConfig
from openhands.core.logger import openhands_logger as logger


class DeepSeekR1Config:
    """Configuration class for DeepSeek R1 models."""

    # Model-specific settings
    DEFAULT_TEMPERATURE = 0.0
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TOP_P = 0.95
    DEFAULT_TIMEOUT = 60

    # R1-specific optimizations
    ENABLE_REASONING_TRACE = True
    ENABLE_STEP_BY_STEP = True
    ENABLE_REFLECTION = True

    # Performance settings
    BATCH_SIZE = 1
    ENABLE_CACHING = True
    CONNECTION_POOL_SIZE = 10

    @classmethod
    def get_optimized_config(
        cls, api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs
    ) -> LLMConfig:
        """
        Get an optimized LLMConfig for DeepSeek R1-0528.

        Args:
            api_key: DeepSeek API key
            base_url: Base URL for DeepSeek API
            **kwargs: Additional configuration parameters

        Returns:
            Optimized LLMConfig for DeepSeek R1
        """
        from pydantic import SecretStr

        # Default base URL for DeepSeek API
        if base_url is None:
            base_url = 'https://api.deepseek.com'

        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('DEEPSEEK_API_KEY')

        config_params = {
            'model': 'deepseek-r1-0528',
            'api_key': SecretStr(api_key) if api_key else None,
            'base_url': base_url,
            'temperature': kwargs.get('temperature', cls.DEFAULT_TEMPERATURE),
            'max_output_tokens': kwargs.get(
                'max_output_tokens', cls.DEFAULT_MAX_TOKENS
            ),
            'top_p': kwargs.get('top_p', cls.DEFAULT_TOP_P),
            'timeout': kwargs.get('timeout', cls.DEFAULT_TIMEOUT),
            'num_retries': kwargs.get('num_retries', 3),
            'retry_min_wait': kwargs.get('retry_min_wait', 1),
            'retry_max_wait': kwargs.get('retry_max_wait', 10),
            'retry_multiplier': kwargs.get('retry_multiplier', 2.0),
            'drop_params': kwargs.get('drop_params', True),
            'modify_params': kwargs.get('modify_params', True),
            'caching_prompt': kwargs.get('caching_prompt', cls.ENABLE_CACHING),
        }

        return LLMConfig(**config_params)


class DeepSeekR1Optimizer:
    """Optimizer for DeepSeek R1 model interactions."""

    def __init__(self, config: LLMConfig):
        """
        Initialize the optimizer.

        Args:
            config: LLM configuration for DeepSeek R1
        """
        self.config = config
        self.reasoning_enabled = DeepSeekR1Config.ENABLE_REASONING_TRACE

    def optimize_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Optimize messages for DeepSeek R1 model.

        Args:
            messages: List of message dictionaries

        Returns:
            Optimized messages
        """
        optimized_messages = []

        for message in messages:
            optimized_message = message.copy()

            # Add reasoning prompts for R1 models
            if message.get('role') == 'user' and self.reasoning_enabled:
                content = message.get('content', '')
                if isinstance(content, str) and content.strip():
                    # Add reasoning instruction for complex tasks
                    if self._is_complex_task(content):
                        optimized_message['content'] = self._add_reasoning_prompt(
                            content
                        )

            optimized_messages.append(optimized_message)

        return optimized_messages

    def _is_complex_task(self, content: str) -> bool:
        """
        Determine if a task is complex and would benefit from reasoning.

        Args:
            content: Message content

        Returns:
            True if task is complex
        """
        complex_indicators = [
            'analyze',
            'debug',
            'fix',
            'implement',
            'create',
            'design',
            'optimize',
            'refactor',
            'solve',
            'calculate',
            'plan',
            'step by step',
            'explain',
            'compare',
            'evaluate',
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in complex_indicators)

    def _add_reasoning_prompt(self, content: str) -> str:
        """
        Add reasoning prompt to enhance R1 model performance.

        Args:
            content: Original content

        Returns:
            Content with reasoning prompt
        """
        reasoning_prompt = (
            'Please think through this step by step and show your reasoning process. '
            'Consider multiple approaches and explain your thought process.\n\n'
        )

        return reasoning_prompt + content

    def optimize_completion_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Optimize completion parameters for DeepSeek R1.

        Args:
            params: Original completion parameters

        Returns:
            Optimized parameters
        """
        optimized_params = params.copy()

        # R1-specific optimizations
        if 'temperature' not in optimized_params:
            optimized_params['temperature'] = DeepSeekR1Config.DEFAULT_TEMPERATURE

        if 'top_p' not in optimized_params:
            optimized_params['top_p'] = DeepSeekR1Config.DEFAULT_TOP_P

        # Enable streaming for better user experience
        if 'stream' not in optimized_params:
            optimized_params['stream'] = (
                False  # Keep False for now, can be enabled later
            )

        return optimized_params


def is_deepseek_r1_model(model_name: str) -> bool:
    """
    Check if a model is a DeepSeek R1 model.

    Args:
        model_name: Name of the model

    Returns:
        True if it's a DeepSeek R1 model
    """
    r1_models = [
        'deepseek-r1-0528',
        'deepseek-r1',
        'deepseek/r1-0528',
        'deepseek/r1',
    ]

    return any(r1_model in model_name.lower() for r1_model in r1_models)


def create_deepseek_r1_llm(
    api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs
) -> Any:
    """
    Create an optimized LLM instance for DeepSeek R1-0528.

    Args:
        api_key: DeepSeek API key
        base_url: Base URL for DeepSeek API
        **kwargs: Additional configuration parameters

    Returns:
        Optimized LLM instance
    """
    from openhands.llm.llm import LLM

    config = DeepSeekR1Config.get_optimized_config(
        api_key=api_key, base_url=base_url, **kwargs
    )

    llm = LLM(config)

    # Add R1-specific optimizations
    optimizer = DeepSeekR1Optimizer(config)

    # Monkey patch the completion method to add optimizations
    original_completion = llm.completion

    def optimized_completion(*args, **kwargs):
        # Optimize messages if provided
        if 'messages' in kwargs:
            kwargs['messages'] = optimizer.optimize_messages(kwargs['messages'])
        elif len(args) > 1:
            # Handle positional arguments
            args_list = list(args)
            if len(args_list) > 1:
                args_list[1] = optimizer.optimize_messages(args_list[1])
            args = tuple(args_list)

        # Optimize completion parameters
        kwargs = optimizer.optimize_completion_params(kwargs)

        return original_completion(*args, **kwargs)

    # Replace the completion method
    setattr(llm, 'completion', optimized_completion)

    logger.info(
        f'Created optimized DeepSeek R1 LLM instance with model: {config.model}'
    )

    return llm


# Cost estimation for DeepSeek R1 models
DEEPSEEK_R1_PRICING = {
    'deepseek-r1-0528': {
        'input_cost_per_token': 0.000014,  # $0.014 per 1K tokens
        'output_cost_per_token': 0.000028,  # $0.028 per 1K tokens
        'reasoning_cost_multiplier': 1.0,  # No additional cost for reasoning tokens
    }
}


def estimate_deepseek_r1_cost(
    input_tokens: int, output_tokens: int, model: str = 'deepseek-r1-0528'
) -> float:
    """
    Estimate the cost for a DeepSeek R1 API call.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name

    Returns:
        Estimated cost in USD
    """
    pricing = DEEPSEEK_R1_PRICING.get(model, DEEPSEEK_R1_PRICING['deepseek-r1-0528'])

    input_cost = input_tokens * pricing['input_cost_per_token']
    output_cost = output_tokens * pricing['output_cost_per_token']

    total_cost = input_cost + output_cost

    logger.debug(
        f'Estimated cost for {model}: ${total_cost:.6f} '
        f'(input: {input_tokens} tokens, output: {output_tokens} tokens)'
    )

    return total_cost
