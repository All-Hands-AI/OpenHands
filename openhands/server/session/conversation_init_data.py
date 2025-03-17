from pydantic import Field

from openhands.integrations.provider import PROVIDER_TOKEN_TYPE
from openhands.server.settings import Settings


class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    This class is immutable to prevent accidental modifications during runtime.
    """

    provider_tokens: PROVIDER_TOKEN_TYPE | None = Field(default_factory=lambda: None)
    selected_repository: str | None = Field(default=None)
    selected_branch: str | None = Field(default=None)

    model_config = {
        "frozen": True,  # Make the model immutable
        "validate_assignment": True,  # Validate values on assignment
        "arbitrary_types_allowed": True,  # Allow custom types like ProviderTokens
    }

    def with_provider_tokens(self, tokens: PROVIDER_TOKEN_TYPE) -> "ConversationInitData":
        """Create a new instance with updated provider tokens."""
        return self.model_copy(update={"provider_tokens": tokens})

    def with_repository(self, repository: str) -> "ConversationInitData":
        """Create a new instance with updated repository."""
        return self.model_copy(update={"selected_repository": repository})

    def with_branch(self, branch: str) -> "ConversationInitData":
        """Create a new instance with updated branch."""
        return self.model_copy(update={"selected_branch": branch})
