from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

from openhands.agent_server.models import SendMessageRequest
from openhands.app_server.event_callback.event_callback_models import (
    EventCallbackProcessor,
)
from openhands.app_server.sandbox.sandbox_models import SandboxStatus
from openhands.app_server.utils.date_utils import utc_now
from openhands.integrations.service_types import ProviderType
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.sdk.llm import MetricsSnapshot
from openhands.storage.data_models.conversation_metadata import ConversationTrigger


class SandboxedConversationInfo(SQLModel, table=True):  # type: ignore
    """Conversation info which does not contain status."""

    id: UUID = SQLField(default=uuid4, primary_key=True)

    selected_repository: str | None
    user_id: str
    selected_branch: str | None = None
    git_provider: ProviderType | None = None
    title: str | None = None
    trigger: ConversationTrigger | None = None
    pr_number: list[int] = Field(default_factory=list)
    llm_model: str | None = None

    metrics: MetricsSnapshot | None = None

    sandbox_id: str = SQLField(index=True)
    created_at: datetime = SQLField(default_factory=utc_now, index=True)
    updated_at: datetime = SQLField(default_factory=utc_now, index=True)


class SandboxedConversationInfoPage(BaseModel):
    items: list[SandboxedConversationInfo]
    next_page_id: str | None = None


class SandboxedConversation(SandboxedConversationInfo):
    sandbox_status: SandboxStatus
    agent_status: AgentExecutionStatus | None


class SandboxedConversationPage(BaseModel):
    items: list[SandboxedConversation]
    next_page_id: str | None = None


class StartSandboxedConversationRequest(BaseModel):
    """Start conversation request object.

    Although a user can go directly to the sandbox and start conversations, they
    would need to manually supply required startup parameters such as LLM key. Starting
    from the app server copies these from the user info.
    """

    sandbox_id: str | None = Field(default=None)
    initial_message: SendMessageRequest | None = None
    processors: list[EventCallbackProcessor] = Field(default_factory=list)
