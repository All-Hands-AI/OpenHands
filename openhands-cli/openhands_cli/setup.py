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
from prompt_toolkit import HTML, print_formatted_text
from pydantic import SecretStr


def setup_agent() -> Conversation:
    """
    Setup the agent with environment variables.
    """
    # Get API configuration from environment
    api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    base_url = os.getenv("LITELLM_BASE_URL")

    if not api_key:
        print_formatted_text(
            HTML(
                "<red>Error: No API key found. Please set LITELLM_API_KEY or OPENAI_API_KEY environment variable.</red>"
            )
        )
        raise Exception(
            "No API key found. Please set LITELLM_API_KEY or OPENAI_API_KEY environment variable."
        )

    llm = LLM(
        model=model,
        api_key=SecretStr(api_key) if api_key else None,
        base_url=base_url,
    )

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
        HTML(f"<green>✓ Agent initialized with model: {model}</green>")
    )
    return conversation
