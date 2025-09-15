import os

from prompt_toolkit import HTML, print_formatted_text

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


def setup_agent() -> Conversation:
    """
    Setup the agent with environment variables.
    """

    llm = LLM.load_from_env()

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
        HTML(f'<green>✓ Agent initialized with model: {llm.model}</green>')
    )
    return conversation
