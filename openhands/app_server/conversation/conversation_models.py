from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from openhands.sdk.llm import MetricsSnapshot
from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel

from openhands.agent_server.models import SendMessageRequest
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.app_server.event_callback.event_callback_models import EventCallbackProcessor
from openhands.app_server.sandbox.sandbox_models import SandboxStatus
from openhands.app_server.utils.date_utils import utc_now
from openhands.integrations.service_types import ProviderType
from openhands.storage.data_models.conversation_metadata import ConversationTrigger


class SandboxedConversationInfo(SQLModel, table=True):
    """Conversation info which does not contain status"""
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
    """Although a user can go directly to the sandbox and start conversations, these
    will lack any of the stored settings for a user. Starting a conversation in the
    app server allows default parameters / secrets to be loaded from settings.
    """

    sandbox_id: str | None = Field(default=None)
    initial_message: SendMessageRequest | None = None
    processors: list[EventCallbackProcessor] = Field(default_factory=list)
