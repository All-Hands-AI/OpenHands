from typing import TYPE_CHECKING

from openhands_cli.tui.settings.store import AgentStore
from openhands_cli.logging_config import suppress_initialization_logs, DEBUG
from prompt_toolkit import HTML, print_formatted_text

if TYPE_CHECKING:
    from openhands.sdk import BaseConversation

class MissingAgentSpec(Exception):
    """Raised when agent specification is not found or invalid."""
    pass

# Global flag to track if tools have been registered
_tools_registered = False

def _register_tools_once():
    """Register tools only once to avoid duplicate registrations."""
    global _tools_registered
    
    if _tools_registered:
        return
    
    from openhands.sdk import register_tool
    from openhands.tools.execute_bash import BashTool
    from openhands.tools.str_replace_editor import FileEditorTool
    from openhands.tools.task_tracker import TaskTrackerTool
    
    # Register tools
    register_tool("BashTool", BashTool)
    register_tool("FileEditorTool", FileEditorTool)
    register_tool("TaskTrackerTool", TaskTrackerTool)
    
    _tools_registered = True

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

    # Suppress logs during initialization unless DEBUG is enabled
    with suppress_initialization_logs():
        # Only import heavy SDK modules when we know we have a valid agent
        from openhands.sdk import Conversation

        # Register tools only once to avoid duplicate registrations
        _register_tools_once()

        # Create conversation - agent context is now set in AgentStore.load()
        conversation = Conversation(agent=agent)

    # Only show initialization message if not in DEBUG mode or if explicitly requested
    if DEBUG:
        print_formatted_text(
            HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
        )
    else:
        # Show a minimal initialization message
        print_formatted_text(
            HTML(f"<green>✓ Agent ready</green>")
        )
    
    return conversation
