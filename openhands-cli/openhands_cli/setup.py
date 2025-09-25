from typing import TYPE_CHECKING

from openhands_cli.tui.settings.store import AgentStore
from prompt_toolkit import HTML, print_formatted_text

if TYPE_CHECKING:
    from openhands.sdk import BaseConversation

class MissingAgentSpec(Exception):
    """Raised when agent specification is not found or invalid."""
    pass

def setup_conversation() -> "BaseConversation":
    """
    Setup the conversation with agent using lazy imports for performance.

    Raises:
        MissingAgentSpec: If agent specification is not found or invalid.
    """
    # Fast check for agent configuration first
    agent_store = AgentStore()
    agent = agent_store.load()
    if not agent:
        raise MissingAgentSpec("Agent specification not found. Please configure your agent settings.")

    # Only import heavy SDK modules when we know we have a valid agent
    from openhands.sdk import Conversation, register_tool
    from openhands.tools.execute_bash import BashTool
    from openhands.tools.str_replace_editor import FileEditorTool
    from openhands.tools.task_tracker import TaskTrackerTool

    # Register tools
    register_tool("BashTool", BashTool)
    register_tool("FileEditorTool", FileEditorTool)
    register_tool("TaskTrackerTool", TaskTrackerTool)

    # Create conversation - agent context is now set in AgentStore.load()
    conversation = Conversation(agent=agent)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
