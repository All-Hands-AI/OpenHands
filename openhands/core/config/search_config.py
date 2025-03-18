"""Configuration for search engine functionality."""

import os
from typing import Any

from pydantic import BaseModel, Field, SecretStr


class SearchConfig(BaseModel):
    """Configuration for search engine functionality.

    Attributes:
        enabled: Whether search engine functionality is enabled.
        api_key: The API key for the search engine.
        api_url: The base URL for the search API.
    """

    enabled: bool = Field(default=False)
    api_key: SecretStr | None = Field(default=None)
    api_url: str = Field(default="https://api.search.brave.com/res/v1/web/search")

    model_config = {"extra": "forbid"}

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to assign search-related variables to environment variables.

        This ensures that these values are accessible to the search engine at runtime.
        """
        super().model_post_init(__context)

        # Set environment variables for search engine
        if self.api_key:
            os.environ["BRAVE_API_KEY"] = self.api_key.get_secret_value()
        if self.api_url:
            os.environ["BRAVE_API_URL"] = self.api_url