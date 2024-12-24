from dataclasses import dataclass

from openhands.server.settings import Settings


@dataclass
class ConversationInitData(Settings):
    """
    Session initialization data for the web environment - a deep copy of the global config is made and then overridden with this data.
    """

    github_token: str | None = None
    selected_repository: str | None = None
