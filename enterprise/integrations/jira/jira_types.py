from abc import ABC, abstractmethod

from integrations.models import JobContext
from jinja2 import Environment
from storage.jira_user import JiraUser
from storage.jira_workspace import JiraWorkspace

from openhands.server.user_auth.user_auth import UserAuth


class JiraViewInterface(ABC):
    """Interface for Jira views that handle different types of Jira interactions."""

    job_context: JobContext
    saas_user_auth: UserAuth
    jira_user: JiraUser
    jira_workspace: JiraWorkspace
    selected_repo: str | None
    conversation_id: str

    @abstractmethod
    def _get_instructions(self, jinja_env: Environment) -> tuple[str, str]:
        """Get initial instructions for the conversation."""
        pass

    @abstractmethod
    async def create_or_update_conversation(self, jinja_env: Environment) -> str:
        """Create or update a conversation and return the conversation ID."""
        pass

    @abstractmethod
    def get_response_msg(self) -> str:
        """Get the response message to send back to Jira."""
        pass


class StartingConvoException(Exception):
    """Exception raised when starting a conversation fails."""

    pass
