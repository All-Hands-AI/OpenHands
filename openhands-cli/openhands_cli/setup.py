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
    include_security_analyzer: bool = True,
    gateway_config_path: str | None = None
) -> BaseConversation:
    """
    Setup the conversation with agent.

    Args:
        conversation_id: conversation ID to use. If not provided, a random UUID will be generated.
        include_security_analyzer: Whether to include the security analyzer
        gateway_config_path: Optional path to gateway configuration file

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

        # Apply gateway configuration if provided
        if gateway_config_path:
            from openhands_cli.gateway_config import load_gateway_config, expand_env_vars
            try:
                gateway_config = load_gateway_config(gateway_config_path)
            except FileNotFoundError as e:
                raise ValueError(
                    f"Gateway configuration file not found: {gateway_config_path}\n"
                    f"Please check the file path or set OPENHANDS_GATEWAY_CONFIG correctly."
                ) from e
            except ValueError as e:
                raise ValueError(
                    f"Invalid gateway configuration file: {e}\n"
                    f"Please ensure {gateway_config_path} is a valid TOML file."
                ) from e

            try:
                gateway_config = expand_env_vars(gateway_config)
            except ValueError as e:
                raise ValueError(
                    f"Failed to expand environment variables in gateway config: {e}\n"
                    f"Make sure all referenced environment variables are set."
                ) from e

            # Update the agent's LLM with gateway configuration
            llm = agent.llm
            # Create a new LLM instance with the gateway config
            from openhands.sdk import LLM
            from openhands_cli.llm_utils import get_llm_metadata

            llm_kwargs = {
                'model': llm.model,
                'api_key': llm.api_key,
                'base_url': llm.base_url,
                'service_id': llm.service_id,
                'metadata': get_llm_metadata(model_name=llm.model, llm_type='agent'),
                **gateway_config  # Add all gateway config fields
            }

            try:
                new_llm = LLM(**llm_kwargs)
                agent = agent.model_copy(update={'llm': new_llm})
                print(f"✓ Gateway configuration loaded from: {gateway_config_path}")
            except Exception as e:
                raise ValueError(
                    f"Failed to apply gateway configuration: {e}\n"
                    f"Please check that all gateway settings in {gateway_config_path} are valid."
                ) from e

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
    resume_conversation_id: str | None = None,
    gateway_config_path: str | None = None
) -> BaseConversation:
    """Start a fresh conversation by creating a new conversation instance.

    Handles the complete conversation setup process including settings screen
    if agent configuration is missing.

    Args:
        resume_conversation_id: Optional conversation ID to resume
        gateway_config_path: Optional path to gateway configuration file

    Returns:
        BaseConversation: A new conversation instance
    """
    conversation = None
    settings_screen = SettingsScreen()
    try:
        conversation = setup_conversation(
            resume_conversation_id,
            gateway_config_path=gateway_config_path
        )
        return conversation
    except MissingAgentSpec:
        # For first-time users, show the full settings flow with choice between basic/advanced
        settings_screen.configure_settings(first_time=True)


    # Try once again after settings setup attempt
    return setup_conversation(
        resume_conversation_id,
        gateway_config_path=gateway_config_path
    )
