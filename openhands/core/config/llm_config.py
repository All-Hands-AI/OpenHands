import os
from dataclasses import dataclass, field, fields
from typing import Any

from openhands.core.config.config_utils import get_field_info

LLM_SENSITIVE_FIELDS = ['api_key', 'aws_access_key_id', 'aws_secret_access_key']


@dataclass
class LLMConfig:
    """Configuration for the LLM model.

    Attributes:
        model: The model to use.
        api_key: The API key to use.
        base_url: The base URL for the API. This is necessary for local LLMs. It is also used for Azure embeddings.
        api_version: The version of the API.
        embedding_model: The embedding model to use.
        embedding_base_url: The base URL for the embedding API.
        embedding_deployment_name: The name of the deployment for the embedding API. This is used for Azure OpenAI.
        aws_access_key_id: The AWS access key ID.
        aws_secret_access_key: The AWS secret access key.
        aws_region_name: The AWS region name.
        num_retries: The number of retries to attempt.
        retry_multiplier: The multiplier for the exponential backoff.
        retry_min_wait: The minimum time to wait between retries, in seconds. This is exponential backoff minimum. For models with very low limits, this can be set to 15-20.
        retry_max_wait: The maximum time to wait between retries, in seconds. This is exponential backoff maximum.
        timeout: The timeout for the API.
        max_message_chars: The approximate max number of characters in the content of an event included in the prompt to the LLM. Larger observations are truncated.
        temperature: The temperature for the API.
        top_p: The top p for the API.
        custom_llm_provider: The custom LLM provider to use. This is undocumented in openhands, and normally not used. It is documented on the litellm side.
        max_input_tokens: The maximum number of input tokens. Note that this is currently unused, and the value at runtime is actually the total tokens in OpenAI (e.g. 128,000 tokens for GPT-4).
        max_output_tokens: The maximum number of output tokens. This is sent to the LLM.
        input_cost_per_token: The cost per input token. This will available in logs for the user to check.
        output_cost_per_token: The cost per output token. This will available in logs for the user to check.
        ollama_base_url: The base URL for the OLLAMA API.
        drop_params: Drop any unmapped (unsupported) params without causing an exception.
        disable_vision: If model is vision capable, this option allows to disable image processing (useful for cost reduction).
        caching_prompt: Use the prompt caching feature if provided by the LLM and supported by the provider.
        log_completions: Whether to log LLM completions to the state.
    """

    model: str = 'gpt-4o'
    api_key: str | None = None
    base_url: str | None = None
    api_version: str | None = None
    embedding_model: str = 'local'
    embedding_base_url: str | None = None
    embedding_deployment_name: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region_name: str | None = None
    openrouter_site_url: str = 'https://docs.all-hands.dev/'
    openrouter_app_name: str = 'OpenHands'
    num_retries: int = 8
    retry_multiplier: float = 2
    retry_min_wait: int = 15
    retry_max_wait: int = 120
    timeout: int | None = None
    max_message_chars: int = 10_000  # maximum number of characters in an observation's content when sent to the llm
    temperature: float = 0.0
    top_p: float = 1.0
    custom_llm_provider: str | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    ollama_base_url: str | None = None
    drop_params: bool = True
    disable_vision: bool | None = None
    caching_prompt: bool = True
    log_completions: bool = False

    # Router-specific configurations
    router_models: list[dict[str, Any]] = field(default_factory=list)
    router_options: dict[str, Any] = field(
        default_factory=lambda: {
            'timeout': 30,
            'max_retries': 10,
        }
    )
    router_routing_strategy: str = 'simple-shuffle'
    router_num_retries: int = 3
    router_cooldown_time: float = 1.0
    router_allowed_fails: int = 5
    router_cache_responses: bool = False
    router_cache_kwargs: dict[str, Any] = field(default_factory=dict)

    def get_litellm_compatible_dict(self) -> dict:
        """Return a dict with only the fields compatible with litellm."""
        compatible_keys = [
            'model',
            'api_key',
            'base_url',
            'api_version',
            'timeout',
            'temperature',
            'top_p',
            'custom_llm_provider',
            'max_output_tokens',
            'drop_params',
        ]
        result = {
            k: v
            for k, v in self.__dict__.items()
            if k in compatible_keys and v is not None
        }

        # Convert max_output_tokens to max_tokens for compatibility
        if 'max_output_tokens' in result:
            result['max_tokens'] = result.pop('max_output_tokens')

        return result

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> 'LLMConfig':
        """Create an LLMConfig instance from a dictionary (e.g., parsed from TOML)."""
        # Filter out keys that are not fields in LLMConfig
        valid_keys = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}

        # Create the LLMConfig instance
        return cls(**filtered_dict)

    def defaults_to_dict(self) -> dict:
        """Serialize fields to a dict for the frontend, including type hints, defaults, and whether it's optional."""
        result = {}
        for f in fields(self):
            result[f.name] = get_field_info(f)
        return result

    def __post_init__(self):
        """
        Post-initialization hook to assign OpenRouter-related variables to environment variables.
        This ensures that these values are accessible to litellm at runtime.
        """

        # Assign OpenRouter-specific variables to environment variables
        if self.openrouter_site_url:
            os.environ['OR_SITE_URL'] = self.openrouter_site_url
        if self.openrouter_app_name:
            os.environ['OR_APP_NAME'] = self.openrouter_app_name

    def __str__(self):
        attr_str = []
        for f in fields(self):
            attr_name = f.name
            attr_value = getattr(self, f.name)

            if attr_name in LLM_SENSITIVE_FIELDS:
                attr_value = '******' if attr_value else None

            attr_str.append(f'{attr_name}={repr(attr_value)}')

        return f"LLMConfig({', '.join(attr_str)})"

    def __repr__(self):
        return self.__str__()

    def to_safe_dict(self):
        """Return a dict with the sensitive fields replaced with ******."""
        ret = self.__dict__.copy()
        for k, v in ret.items():
            if k in LLM_SENSITIVE_FIELDS:
                ret[k] = '******' if v else None
        return ret
