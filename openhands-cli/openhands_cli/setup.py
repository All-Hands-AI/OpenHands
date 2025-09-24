from openhands_cli.tui.settings.store import AgentStore


def _register_tools():
    """Register tools lazily when needed."""
    from openhands.tools.execute_bash import BashTool
    from openhands.tools.str_replace_editor import FileEditorTool
    from openhands.tools.task_tracker import TaskTrackerTool
    from openhands.sdk import register_tool

    register_tool("BashTool", BashTool)
    register_tool("FileEditorTool", FileEditorTool)
    register_tool("TaskTrackerTool", TaskTrackerTool)

def setup_agent():
    """
    Setup the agent with environment variables.
    """
    # Lazy imports to avoid startup cost
    from openhands.sdk import Agent, Conversation
    from prompt_toolkit import HTML, print_formatted_text

    agent_store = AgentStore()
    agent = agent_store.load()
    if not agent:
        return None

    # Register tools when actually setting up agent
    _register_tools()

    # Create agent
    conversation = Conversation(agent=agent)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
