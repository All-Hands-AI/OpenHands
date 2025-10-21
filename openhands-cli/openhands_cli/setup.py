import uuid

from prompt_toolkit import HTML, print_formatted_text

from openhands.sdk import BaseConversation, Conversation, Workspace, register_tool
from openhands.tools.execute_bash import BashTool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands_cli.listeners import LoadingContext
from openhands_cli.locations import CONVERSATIONS_DIR, WORK_DIR
from openhands_cli.tui.settings.store import AgentStore
from openhands.sdk.security.confirmation_policy import (
    AlwaysConfirm,
)
from openhands_cli.tui.settings.settings_screen import SettingsScreen


register_tool('BashTool', BashTool)
register_tool('FileEditorTool', FileEditorTool)
register_tool('TaskTrackerTool', TaskTrackerTool)


class MissingAgentSpec(Exception):
    """Raised when agent specification is not found or invalid."""

    pass


def setup_conversation(
    conversation_id: str | None = None,
    include_security_analyzer: bool = True
) -> BaseConversation:
    """
    Setup the conversation with agent.

    Args:
        conversation_id: conversation ID to use. If not provided, a random UUID will be generated.

    Raises:
        MissingAgentSpec: If agent specification is not found or invalid.
    """

    # Use provided conversation_id or generate a random one
    if conversation_id is None:
        conversation_id = uuid.uuid4()
    elif isinstance(conversation_id, str):
        try:
            conversation_id = uuid.UUID(conversation_id)
        except ValueError as e:
            print_formatted_text(
                HTML(
                    f"<yellow>Warning: '{conversation_id}' is not a valid UUID.</yellow>"
                )
            )
            raise e

    with LoadingContext('Initializing OpenHands agent...'):
        agent_store = AgentStore()
        agent = agent_store.load(session_id=str(conversation_id))
        if not agent:
            raise MissingAgentSpec(
                'Agent specification not found. Please configure your agent settings.'
            )


        if not include_security_analyzer:
            # Remove security analyzer from agent spec
            agent = agent.model_copy(
                update={"security_analyzer": None}
            )

        # Create conversation - agent context is now set in AgentStore.load()
        conversation: BaseConversation = Conversation(
            agent=agent,
            workspace=Workspace(working_dir=WORK_DIR),
            # Conversation will add /<conversation_id> to this path
            persistence_dir=CONVERSATIONS_DIR,
            conversation_id=conversation_id,
        )

        if include_security_analyzer:
            conversation.set_confirmation_policy(AlwaysConfirm())

    print_formatted_text(
        HTML(f'<green>✓ Agent initialized with model: {agent.llm.model}</green>')
    )
    return conversation



def start_fresh_conversation(
    resume_conversation_id: str | None = None
) -> BaseConversation:
    """Start a fresh conversation by creating a new conversation instance.

    Handles the complete conversation setup process including settings screen
    if agent configuration is missing.

    Args:
        resume_conversation_id: Optional conversation ID to resume

    Returns:
        BaseConversation: A new conversation instance
    """
    conversation = None
    settings_screen = SettingsScreen()
    try:
        conversation = setup_conversation(resume_conversation_id)
        return conversation
    except MissingAgentSpec:
        # For first-time users, show the full settings flow with choice between basic/advanced
        settings_screen.configure_settings(first_time=True)


    # Try once again after settings setup attempt
    return setup_conversation(resume_conversation_id)
