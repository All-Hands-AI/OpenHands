from pydantic import BaseModel, Field, SecretStr


class SearchConfig(BaseModel):
    """Configuration for search engines.

    Attributes:
        brave_api_key: API key for Brave Search API.
        brave_api_url: Base URL for Brave Search API.
    """

    brave_api_key: SecretStr | None = Field(default=None)
    brave_api_url: str = Field(
        default='https://api.search.brave.com/res/v1/web/search'
    )

    model_config = {'extra': 'forbid'}