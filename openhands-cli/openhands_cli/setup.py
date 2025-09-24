from openhands.sdk import (
    Agent,
    Conversation
)
from openhands_cli.tui.settings.store import AgentStore
from prompt_toolkit import HTML, print_formatted_text
from openhands.tools.execute_bash import BashTool
from openhands.tools.str_replace_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.sdk import register_tool

register_tool("BashTool", BashTool)
register_tool("FileEditorTool", FileEditorTool)
register_tool("TaskTrackerTool", TaskTrackerTool)

def setup_agent() -> Conversation | None:
    """
    Setup the agent with environment variables.
    """

    agent_store = AgentStore()
    agent = agent_store.load()
    if not agent:
        return None

    # Create agent
    conversation = Conversation(agent=agent)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
