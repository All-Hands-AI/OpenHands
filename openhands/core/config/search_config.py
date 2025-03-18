from pydantic import BaseModel, Field


class SearchConfig(BaseModel):
    """Configuration for search engines.

    Attributes:
        enable_search_engine: Whether to enable the search engine feature.
        brave_api_key: The API key for Brave Search.
        brave_api_url: The URL for the Brave Search API.
    """

    enable_search_engine: bool = Field(default=False)
    brave_api_key: str | None = Field(default=None)
    brave_api_url: str = Field(default='https://api.search.brave.com/res/v1/web/search')

    model_config = {'extra': 'forbid'}
