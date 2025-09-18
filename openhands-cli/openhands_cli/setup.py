from openhands.sdk import (
    Agent,
    Conversation
)
from openhands_cli.tui.settings.store import AgentSpecStore
from prompt_toolkit import HTML, print_formatted_text


def setup_agent() -> Conversation | None:
    """
    Setup the agent with environment variables.
    """

    spec_store = AgentSpecStore()
    spec = spec_store.load()
    if not spec:
        return None

    # Create agent
    agent = Agent.from_spec(spec)
    conversation = Conversation(agent=agent)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {agent.llm.model}</green>")
    )
    return conversation
