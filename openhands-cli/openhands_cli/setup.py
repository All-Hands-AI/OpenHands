import os

from prompt_toolkit import HTML, print_formatted_text
from pydantic import SecretStr

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
from openhands_cli.settings import SettingsManager


def setup_agent() -> Conversation:
    """
    Setup the agent with persistent settings and environment variable overrides.
    """
    # Load settings from persistent storage with environment variable overrides
    settings_manager = SettingsManager()
    settings = settings_manager.get_effective_settings()
    
    # Extract configuration
    api_key = settings.api_key.get_secret_value() if settings.api_key else None
    model = settings.model
    base_url = settings.base_url

    if not api_key:
        print_formatted_text(
            HTML(
                '<red>Error: No API key found. Please configure it using /settings command or set LITELLM_API_KEY/OPENAI_API_KEY environment variable.</red>'
            )
        )
        raise Exception(
            'No API key found. Please configure it using /settings command or set LITELLM_API_KEY/OPENAI_API_KEY environment variable.'
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
        HTML(f'<green>✓ Agent initialized with model: {model}</green>')
    )
    return conversation
