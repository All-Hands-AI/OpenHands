from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column
from sqlmodel import JSON, SQLModel
from sqlmodel import Field as SQLField

from openhands.agent_server.models import SendMessageRequest
from openhands.agent_server.utils import utc_now
from openhands.app_server.event_callback.event_callback_models import (
    EventCallbackProcessor,
)
from openhands.app_server.sandbox.sandbox_models import SandboxStatus
from openhands.app_server.utils.sql_utils import create_json_type_decorator
from openhands.integrations.service_types import ProviderType
from openhands.sdk.conversation.state import AgentExecutionStatus
from openhands.sdk.llm import MetricsSnapshot
from openhands.storage.data_models.conversation_metadata import ConversationTrigger


class AppConversationInfo(SQLModel, table=True):  # type: ignore
    """Conversation info which does not contain status."""

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)

    user_id: str

    selected_repository: str | None = None
    selected_branch: str | None = None
    git_provider: ProviderType | None = None
    title: str | None = None
    trigger: ConversationTrigger | None = None
    pr_number: list[int] = SQLField(default_factory=list, sa_column=Column(JSON))
    llm_model: str | None = None

    metrics: MetricsSnapshot | None = SQLField(default=None, sa_column=Column(JSON))

    sandbox_id: str = SQLField(index=True)
    created_at: datetime = SQLField(default_factory=utc_now, index=True)
    updated_at: datetime = SQLField(default_factory=utc_now, index=True)


class AppConversationSortOrder(Enum):
    CREATED_AT = 'CREATED_AT'
    CREATED_AT_DESC = 'CREATED_AT_DESC'
    UPDATED_AT = 'UPDATED_AT'
    UPDATED_AT_DESC = 'UPDATED_AT_DESC'
    TITLE = 'TITLE'
    TITLE_DESC = 'TITLE_DESC'


class AppConversationInfoPage(BaseModel):
    items: list[AppConversationInfo]
    next_page_id: str | None = None


class AppConversation(AppConversationInfo):  # type: ignore
    sandbox_status: SandboxStatus = Field(
        default=SandboxStatus.MISSING,
        description='Current sandbox status. Will be MISSING if the sandbox does not exist.',
    )
    agent_status: AgentExecutionStatus | None = Field(
        default=None,
        description='Current agent status. Will be None if the sandbox_status is not RUNNING',
    )

    # Have to redefine these due to a bug in SQLModel :(
    pr_number: list[int] = SQLField(default_factory=list, sa_column=Column(JSON))
    metrics: MetricsSnapshot | None = SQLField(default=None, sa_column=Column(JSON))


class AppConversationPage(BaseModel):
    items: list[AppConversation]
    next_page_id: str | None = None


class AppConversationStartRequest(BaseModel):
    """Start conversation request object.

    Although a user can go directly to the sandbox and start conversations, they
    would need to manually supply required startup parameters such as LLM key. Starting
    from the app server copies these from the user info.
    """

    sandbox_id: str | None = Field(default=None)
    initial_message: SendMessageRequest | None = None
    processors: list[EventCallbackProcessor] = Field(default_factory=list)


class AppConversationStartTaskStatus(Enum):
    WORKING = 'WORKING'
    WAITING_FOR_SANDBOX = 'WAITING_FOR_SANDBOX'
    STARTING_CONVERSATION = 'STARTING_CONVERSATION'
    READY = 'READY'
    ERROR = 'ERROR'


class AppConversationStartTask(SQLModel, table=True):  # type: ignore
    """Object describing the start process for an app conversation.

    Because starting an app conversation can be slow (And can involve starting a sandbox),
    we kick off a background task for it. Once the conversation is started, the app_conversation_id
    is populated."""

    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    user_id: str = SQLField(index=True)
    status: AppConversationStartTaskStatus = AppConversationStartTaskStatus.WORKING
    detail: str | None = None
    app_conversation_id: UUID | None = SQLField(
        default=None, description='The id of the app_conversation, if READY'
    )
    sandbox_id: str | None = SQLField(
        default=None, description='The id of the sandbox, if READY'
    )
    agent_server_url: str | None = SQLField(
        default=None, description='The agent server url, if READY'
    )
    request: AppConversationStartRequest = SQLField(
        sa_column=Column(create_json_type_decorator(AppConversationStartRequest))
    )
    created_at: datetime = SQLField(default_factory=utc_now, index=True)
    updated_at: datetime = SQLField(default_factory=utc_now, index=True)
