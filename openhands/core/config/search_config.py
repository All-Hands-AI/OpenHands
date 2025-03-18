from pydantic import BaseModel, Field


class SearchConfig(BaseModel):
    """Configuration for search engines.

    Attributes:
        brave_api_key: The API key for Brave Search.
        brave_api_url: The URL for the Brave Search API.
    """

    brave_api_key: str | None = Field(default=None)
    brave_api_url: str = Field(default='https://api.search.brave.com/res/v1/web/search')

    model_config = {'extra': 'forbid'}
