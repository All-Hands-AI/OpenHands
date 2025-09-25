from openhands.sdk import (
    Conversation,
    BaseConversation
)
from openhands_cli.tui.settings.store import AgentStore
from prompt_toolkit import HTML, print_formatted_text
from openhands.tools.execute_bash import BashTool
from openhands.tools.str_replace_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.sdk import register_tool, LocalFileStore
from openhands_cli.locations import CONVERSATION_PATH
import uuid

register_tool("BashTool", BashTool)
register_tool("FileEditorTool", FileEditorTool)
register_tool("TaskTrackerTool", TaskTrackerTool)


class MissingAgentSpec(Exception):
    """Raised when agent specification is not found or invalid."""
    pass

def setup_conversation() -> BaseConversation:
    """
    Setup the conversation with agent.

    Raises:
        MissingAgentSpec: If agent specification is not found or invalid.
    """

    conversation_id = str(uuid.uuid4())

    agent_store = AgentStore()
    agent = agent_store.load()
    if not agent:
        raise MissingAgentSpec("Agent specification not found. Please configure your agent settings.")

    # Create conversation - agent context is now set in AgentStore.load()
    conversation = Conversation(
        agent=agent,
        persist_filestore=LocalFileStore(CONVERSATION_PATH.format(conversation_id)),
        conversation_id=conversation_id)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
