import os

from openhands.sdk import (
    LLM,
    Agent,
    Conversation,
    Tool,
)
from openhands.tools import (
    BashExecutor,
    FileEditorExecutor,
    execute_bash_tool,
    str_replace_editor_tool,
)
from openhands_cli.locations import LLM_SETTINGS_PATH
from prompt_toolkit import HTML, print_formatted_text


def setup_agent() -> Conversation | None:
    """
    Setup the agent with environment variables.
    """

    try:
        llm = LLM.load_from_json(LLM_SETTINGS_PATH)
    except FileNotFoundError:
        return None

    # Setup tools
    cwd = os.getcwd()
    bash = BashExecutor(working_dir=cwd)
    file_editor = FileEditorExecutor()
    tools: list[Tool] = [
        execute_bash_tool.set_executor(executor=bash),
        str_replace_editor_tool.set_executor(executor=file_editor),
    ]

    # Create agent
    agent = Agent(llm=llm, tools=tools)
    conversation = Conversation(agent=agent)

    print_formatted_text(
        HTML(f"<green>✓ Agent initialized with model: {llm.model}</green>")
    )
    return conversation
