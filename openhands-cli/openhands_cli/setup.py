from openhands.sdk import (
    AgentContext,
    Conversation,
    BaseConversation
)
from openhands_cli.locations import WORK_DIR
from openhands_cli.tui.settings.store import AgentStore
from prompt_toolkit import HTML, print_formatted_text
from openhands.tools.execute_bash import BashTool
from openhands.tools.str_replace_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.sdk import register_tool

register_tool("BashTool", BashTool)
register_tool("FileEditorTool", FileEditorTool)
register_tool("TaskTrackerTool", TaskTrackerTool)

def setup_agent() -> BaseConversation | None:
    """
    Setup the agent with environment variables.
    """

    agent_store = AgentStore()
    agent = agent_store.load()
    if not agent:
        return None

    agent_context = AgentContext(
        system_message_suffix=f"You current working directory is: {WORK_DIR}",
    )

    # Create agent
    conversation = Conversation(agent=agent.model_copy(update={"agent_context": agent_context}))

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
