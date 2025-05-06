from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


class SearchEngineConfig(BaseModel):
    """Configuration for the search engine."""

    type: str = Field(default='mcp_sse')
    url: Optional[str] = Field(default=None)
    tools: Optional[list[str]] = Field(default=[])
    api_key: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default='google')

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'SearchEngineConfig']:
        """Create a mapping of SearchEngineConfig instances from a toml dictionary representing the [search_engine] section.

        The configuration is built from all keys in data.
        """
        search_engine_mapping: dict[str, SearchEngineConfig] = {}
        try:
            search_engine_config: dict[str, Any] = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    search_engine_config[key] = value
            for name, config in search_engine_config.items():
                config['name'] = name
                search_engine_mapping[name] = cls.model_validate(config)

        except ValidationError as e:
            raise ValueError(f'Invalid search engine configuration: {e}')

        return search_engine_mapping
