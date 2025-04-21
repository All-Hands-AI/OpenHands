import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import toml
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.application import Application
from prompt_toolkit.completion import (
    Completer,
    Completion,
    FuzzyWordCompleter,
)
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import clear, print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea
from pydantic import SecretStr

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.controller import AgentController
from openhands.controller.agent import Agent
from openhands.core.cli_display import (
    COLOR_GOLD,
    COLOR_GREY,
    COMMANDS,
    DEFAULT_STYLE,
    UsageMetrics,
    display_banner,
    display_event,
    display_help,
    display_initialization_animation,
    display_runtime_initialization_message,
    display_settings,
    display_shutdown_message,
    display_status,
    display_welcome_message,
)
from openhands.core.cli_utils import (
    VERIFIED_ANTHROPIC_MODELS,
    VERIFIED_OPENAI_MODELS,
    VERIFIED_PROVIDERS,
    organize_models_and_providers,
)
from openhands.core.config import (
    AppConfig,
    parse_arguments,
    setup_config_from_args,
)
from openhands.core.config.condenser_config import NoOpCondenserConfig
from openhands.core.config.utils import OH_DEFAULT_AGENT
from openhands.core.logger import openhands_logger as logger
from openhands.core.loop import run_agent_until_done
from openhands.core.schema import AgentState
from openhands.core.setup import (
    create_agent,
    create_controller,
    create_memory,
    create_runtime,
    initialize_repository_for_runtime,
)
from openhands.events import EventSource, EventStreamSubscriber
from openhands.events.action import (
    Action,
    ChangeAgentStateAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
)
from openhands.io import read_task
from openhands.llm.metrics import Metrics
from openhands.mcp import fetch_mcp_tools_from_config
from openhands.memory.condenser.impl.llm_summarizing_condenser import (
    LLMSummarizingCondenserConfig,
)
from openhands.microagent.microagent import BaseMicroagent
from openhands.runtime.base import Runtime
from openhands.storage.data_models.settings import Settings
from openhands.storage.settings.file_settings_store import FileSettingsStore
from openhands.utils.llm import get_supported_llm_models

REPO_MD_CREATE_PROMPT = """
Please explore this repository. Create the file .openhands/microagents/repo.md with:
- A description of the project
- An overview of the file structure
- Any information on how to run tests or other relevant commands
- Any other information that would be helpful to a brand new developer
Keep it short--just a few paragraphs will do.
"""


class CommandCompleter(Completer):
    """Custom completer for commands."""

    def get_completions(self, document, complete_event):
        text = document.text

        # Only show completions if the user has typed '/'
        if text.startswith('/'):
            # If just '/' is typed, show all commands
            if text == '/':
                for command, description in COMMANDS.items():
                    yield Completion(
                        command[1:],  # Remove the leading '/' as it's already typed
                        start_position=0,
                        display=f'{command} - {description}',
                    )
            # Otherwise show matching commands
            else:
                for command, description in COMMANDS.items():
                    if command.startswith(text):
                        yield Completion(
                            command[len(text) :],  # Complete the remaining part
                            start_position=0,
                            display=f'{command} - {description}',
                        )


prompt_session = PromptSession(style=DEFAULT_STYLE, completer=CommandCompleter())


async def read_prompt_input(multiline=False):
    try:
        if multiline:
            kb = KeyBindings()

            @kb.add('c-d')
            def _(event):
                event.current_buffer.validate_and_handle()

            with patch_stdout():
                message = await prompt_session.prompt_async(
                    'Enter your message and press Ctrl+D to finish:\n',
                    multiline=True,
                    key_bindings=kb,
                )
        else:
            with patch_stdout():
                message = await prompt_session.prompt_async(
                    '> ',
                )
        return message
    except (KeyboardInterrupt, EOFError):
        return '/exit'


async def read_confirmation_input():
    try:
        confirmation = await prompt_session.prompt_async(
            'Confirm action (possible security risk)? (y/n) > ',
        )
        return confirmation.lower() == 'y'
    except (KeyboardInterrupt, EOFError):
        return False


async def init_repository(current_dir: str) -> bool:
    repo_file_path = Path(current_dir) / '.openhands' / 'microagents' / 'repo.md'
    init_repo = False

    if repo_file_path.exists():
        try:
            content = await asyncio.get_event_loop().run_in_executor(
                None, read_file, repo_file_path
            )

            print_formatted_text(
                'Repository instructions file (repo.md) already exists.\n'
            )

            container = Frame(
                TextArea(
                    text=content,
                    read_only=True,
                    style=COLOR_GREY,
                    wrap_lines=True,
                ),
                title='Repository Instructions (repo.md)',
                style=f'fg:{COLOR_GREY}',
            )
            print_container(container)
            print_formatted_text('')  # Add a newline after the frame

            init_repo = (
                cli_confirm(
                    'Do you want to re-initialize?',
                    ['Yes, re-initialize', 'No, dismiss'],
                )
                == 0
            )

            if init_repo:
                write_to_file(repo_file_path, '')
        except Exception:
            print_formatted_text('Error reading repository instructions file (repo.md)')
            init_repo = False
    else:
        print_formatted_text(
            '\nRepository instructions file will be created by exploring the repository.\n'
        )

        init_repo = (
            cli_confirm(
                'Do you want to proceed?',
                ['Yes, create', 'No, dismiss'],
            )
            == 0
        )

    return init_repo


def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def write_to_file(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)


def cli_confirm(
    question: str = 'Are you sure?', choices: Optional[List[str]] = None
) -> int:
    """
    Display a confirmation prompt with the given question and choices.
    Returns the index of the selected choice.
    """

    if choices is None:
        choices = ['Yes', 'No']
    selected = [0]  # Using list to allow modification in closure

    def get_choice_text():
        return [
            ('class:question', f'{question}\n\n'),
        ] + [
            (
                'class:selected' if i == selected[0] else 'class:unselected',
                f"{'> ' if i == selected[0] else '  '}{choice}\n",
            )
            for i, choice in enumerate(choices)
        ]

    kb = KeyBindings()

    @kb.add('up')
    def _(event):
        selected[0] = (selected[0] - 1) % len(choices)

    @kb.add('down')
    def _(event):
        selected[0] = (selected[0] + 1) % len(choices)

    @kb.add('enter')
    def _(event):
        event.app.exit(result=selected[0])

    style = Style.from_dict({'selected': COLOR_GOLD, 'unselected': ''})

    layout = Layout(
        HSplit(
            [
                Window(
                    FormattedTextControl(get_choice_text),
                    always_hide_cursor=True,
                )
            ]
        )
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=style,
        mouse_support=True,
        full_screen=False,
    )

    return app.run(in_thread=True)


def update_usage_metrics(event: Event, usage_metrics: UsageMetrics):
    if not hasattr(event, 'llm_metrics'):
        return

    llm_metrics: Metrics | None = getattr(event, 'llm_metrics', None)
    if not llm_metrics:
        return

    cost = getattr(llm_metrics, 'accumulated_cost', 0)
    usage_metrics.total_cost += cost if isinstance(cost, float) else 0

    token_usage = getattr(llm_metrics, 'accumulated_token_usage', None)
    if not token_usage:
        return

    prompt_tokens = getattr(token_usage, 'prompt_tokens', 0)
    completion_tokens = getattr(token_usage, 'completion_tokens', 0)
    cache_read = getattr(token_usage, 'cache_read_tokens', 0)
    cache_write = getattr(token_usage, 'cache_write_tokens', 0)

    usage_metrics.total_input_tokens += (
        prompt_tokens if isinstance(prompt_tokens, int) else 0
    )
    usage_metrics.total_output_tokens += (
        completion_tokens if isinstance(completion_tokens, int) else 0
    )
    usage_metrics.total_cache_read += cache_read if isinstance(cache_read, int) else 0
    usage_metrics.total_cache_write += (
        cache_write if isinstance(cache_write, int) else 0
    )


def manage_openhands_file(folder_path=None, add_to_trusted=False):
    openhands_file = Path.home() / '.openhands.toml'
    default_content: dict = {'trusted_dirs': []}

    if not openhands_file.exists():
        with open(openhands_file, 'w') as f:
            toml.dump(default_content, f)

    if folder_path:
        with open(openhands_file, 'r') as f:
            try:
                config = toml.load(f)
            except Exception:
                config = default_content

        if 'trusted_dirs' not in config:
            config['trusted_dirs'] = []

        if folder_path in config['trusted_dirs']:
            return True

        if add_to_trusted:
            config['trusted_dirs'].append(folder_path)
            with open(openhands_file, 'w') as f:
                toml.dump(config, f)

        return False

    return False


def check_folder_security_agreement(current_dir):
    is_trusted = manage_openhands_file(current_dir)

    if not is_trusted:
        security_frame = Frame(
            TextArea(
                text=(
                    f' Do you trust the files in this folder?\n\n'
                    f'   {current_dir}\n\n'
                    ' OpenHands may read and execute files in this folder with your permission.'
                ),
                style=COLOR_GREY,
                read_only=True,
                wrap_lines=True,
            ),
            style=f'fg:{COLOR_GREY}',
        )

        clear()
        print_container(security_frame)
        print_formatted_text('')

        confirm = (
            cli_confirm('Do you wish to continue?', ['Yes, proceed', 'No, exit']) == 0
        )

        if confirm:
            manage_openhands_file(current_dir, add_to_trusted=True)

        return confirm

    return True


async def cleanup_session(
    loop: asyncio.AbstractEventLoop,
    agent: Agent,
    runtime: Runtime,
    controller: AgentController,
):
    """Clean up all resources from the current session."""
    try:
        # Cancel all running tasks except the current one
        current_task = asyncio.current_task(loop)
        pending = [task for task in asyncio.all_tasks(loop) if task is not current_task]
        for task in pending:
            task.cancel()

        # Wait for all tasks to complete with a timeout
        if pending:
            await asyncio.wait(pending, timeout=5.0)

        # Reset agent, close runtime and controller
        agent.reset()
        runtime.close()
        await controller.close()
    except Exception as e:
        logger.error(f'Error during session cleanup: {e}')


class UserCancelledError(Exception):
    """Raised when the user cancels an operation via key binding."""

    pass


def kb_cancel():
    """Custom key bindings to handle ESC as a user cancellation."""
    bindings = KeyBindings()

    @bindings.add('escape')
    def _(event):
        event.app.exit(exception=UserCancelledError, style='class:aborting')

    return bindings


async def modify_llm_settings_basic(
    config: AppConfig, settings_store: FileSettingsStore
) -> bool:
    model_list = get_supported_llm_models(config)
    organized_models = organize_models_and_providers(model_list)

    provider_list = list(organized_models.keys())
    verified_providers = [p for p in VERIFIED_PROVIDERS if p in provider_list]
    provider_list = [p for p in provider_list if p not in verified_providers]
    provider_list = verified_providers + provider_list

    provider_completer = FuzzyWordCompleter(provider_list)
    session = PromptSession(key_bindings=kb_cancel())

    provider = None
    model = None
    api_key = None

    try:
        provider = await session.prompt_async(
            '(Step 1/3) Select LLM Provider (use Tab for completion): ',
            completer=provider_completer,
        )

        if provider not in organized_models:
            print_formatted_text(
                HTML(f'\n<grey>Invalid provider selected: {provider}</grey>\n')
            )
            return False

        model_list = organized_models[provider]['models']
        if provider == 'openai':
            model_list = [m for m in model_list if m not in VERIFIED_OPENAI_MODELS]
            model_list = VERIFIED_OPENAI_MODELS + model_list
        if provider == 'anthropic':
            model_list = [m for m in model_list if m not in VERIFIED_ANTHROPIC_MODELS]
            model_list = VERIFIED_ANTHROPIC_MODELS + model_list

        model_completer = FuzzyWordCompleter(model_list)
        model = await session.prompt_async(
            '(Step 2/3) Select LLM Model (use Tab for completion): ',
            completer=model_completer,
        )

        if model not in organized_models[provider]['models']:
            print_formatted_text(
                HTML(
                    f'\n<grey>Invalid model selected: {model} for provider {provider}</grey>\n'
                )
            )
            return False

        session.completer = None  # Reset completer for password prompt
        api_key = await session.prompt_async('(Step 3/3) Enter API Key: ')

    except (
        UserCancelledError,
        KeyboardInterrupt,
        EOFError,
    ):
        return False  # Return False on exception

    # TODO: check for empty string inputs?
    # Handle case where a prompt might return None unexpectedly
    if provider is None or model is None or api_key is None:
        return False

    save_settings = (
        cli_confirm(
            '\nSave new settings? Current session will be terminated!',
            ['Yes, proceed', 'No, dismiss'],
        )
        == 0
    )

    if not save_settings:
        return False

    llm_config = config.get_llm_config()
    llm_config.model = provider + organized_models[provider]['separator'] + model
    llm_config.api_key = SecretStr(api_key)
    llm_config.base_url = None
    config.set_llm_config(llm_config)

    config.default_agent = OH_DEFAULT_AGENT
    config.security.confirmation_mode = False
    config.enable_default_condenser = True

    agent_config = config.get_agent_config(config.default_agent)
    agent_config.condenser = LLMSummarizingCondenserConfig(
        llm_config=llm_config,
        type='llm',
    )
    config.set_agent_config(agent_config, config.default_agent)

    settings = await settings_store.load()
    if not settings:
        settings = Settings()

    settings.llm_model = provider + organized_models[provider]['separator'] + model
    settings.llm_api_key = SecretStr(api_key)
    settings.llm_base_url = None
    settings.agent = OH_DEFAULT_AGENT
    settings.confirmation_mode = False
    settings.enable_default_condenser = True

    await settings_store.store(settings)

    return True


async def modify_llm_settings_advanced(
    config: AppConfig, settings_store: FileSettingsStore
) -> bool:
    session = PromptSession(key_bindings=kb_cancel())

    custom_model = None
    base_url = None
    api_key = None
    agent = None

    try:
        custom_model = await session.prompt_async('(Step 1/6) Custom Model: ')
        base_url = await session.prompt_async('(Step 2/6) Base URL: ')
        api_key = await session.prompt_async('(Step 3/6) API Key: ')

        agent_list = Agent.list_agents()
        agent_completer = FuzzyWordCompleter(agent_list)
        agent = await session.prompt_async(
            '(Step 4/6) Agent (use Tab for completion): ', completer=agent_completer
        )

        if agent not in agent_list:
            print_formatted_text(
                HTML(f'\n<grey>Invalid agent selected: {agent}</grey>\n')
            )
            return False

        enable_confirmation_mode = (
            cli_confirm(
                question='(Step 5/6) Confirmation Mode:',
                choices=['Enable', 'Disable'],
            )
            == 0
        )

        enable_memory_condensation = (
            cli_confirm(
                question='(Step 6/6) Memory Condensation:',
                choices=['Enable', 'Disable'],
            )
            == 0
        )

    except (
        UserCancelledError,
        KeyboardInterrupt,
        EOFError,
    ):
        return False  # Return False on exception

    # TODO: check for empty string inputs?
    # Handle case where a prompt might return None unexpectedly
    if custom_model is None or base_url is None or api_key is None or agent is None:
        return False

    save_settings = (
        cli_confirm(
            '\nSave new settings? Current session will be terminated!',
            ['Yes, proceed', 'No, dismiss'],
        )
        == 0
    )

    if not save_settings:
        return False

    llm_config = config.get_llm_config()
    llm_config.model = custom_model
    llm_config.base_url = base_url
    llm_config.api_key = SecretStr(api_key)
    config.set_llm_config(llm_config)

    config.default_agent = agent

    config.security.confirmation_mode = enable_confirmation_mode

    agent_config = config.get_agent_config(config.default_agent)
    if enable_memory_condensation:
        agent_config.condenser = LLMSummarizingCondenserConfig(
            llm_config=llm_config,
            type='llm',
        )
    else:
        agent_config.condenser = NoOpCondenserConfig(type='noop')
    config.set_agent_config(agent_config)

    settings = await settings_store.load()
    if not settings:
        settings = Settings()

    settings.llm_model = custom_model
    settings.llm_api_key = SecretStr(api_key)
    settings.llm_base_url = base_url
    settings.agent = agent
    settings.confirmation_mode = enable_confirmation_mode
    settings.enable_default_condenser = enable_memory_condensation

    await settings_store.store(settings)

    return True


async def run_session(
    loop: asyncio.AbstractEventLoop,
    config: AppConfig,
    settings_store: FileSettingsStore,
    current_dir: str,
    initial_user_action: Optional[Action] = None,
) -> bool:
    reload_microagents = False
    new_session_requested = False

    sid = str(uuid4())
    is_loaded = asyncio.Event()

    # Show runtime initialization message
    display_runtime_initialization_message(config.runtime)

    # Show Initialization loader
    loop.run_in_executor(
        None, display_initialization_animation, 'Initializing...', is_loaded
    )

    agent = create_agent(config)
    mcp_tools = await fetch_mcp_tools_from_config(config.mcp)
    agent.set_mcp_tools(mcp_tools)
    runtime = create_runtime(
        config,
        sid=sid,
        headless_mode=True,
        agent=agent,
    )

    controller, _ = create_controller(agent, runtime, config)

    event_stream = runtime.event_stream

    usage_metrics = UsageMetrics()

    async def prompt_for_next_task():
        nonlocal reload_microagents, new_session_requested
        while True:
            next_message = await read_prompt_input(config.cli_multiline_input)

            if not next_message.strip():
                continue

            if next_message == '/exit':
                confirm_exit = (
                    cli_confirm('\nTerminate session?', ['Yes, proceed', 'No, dismiss'])
                    == 0
                )

                if not confirm_exit:
                    continue

                event_stream.add_event(
                    ChangeAgentStateAction(AgentState.STOPPED),
                    EventSource.ENVIRONMENT,
                )
                display_shutdown_message(usage_metrics, sid)
                return
            elif next_message == '/help':
                display_help()
                continue
            elif next_message == '/init':
                if config.runtime == 'local':
                    init_repo = await init_repository(current_dir)
                    if init_repo:
                        event_stream.add_event(
                            MessageAction(content=REPO_MD_CREATE_PROMPT),
                            EventSource.USER,
                        )
                        reload_microagents = True
                        return
                else:
                    print_formatted_text(
                        '\nRepository initialization through the CLI is only supported for local runtime.\n'
                    )
                continue
            elif next_message == '/status':
                display_status(usage_metrics, sid)
                continue
            elif next_message == '/new':
                new_session_requested = (
                    cli_confirm(
                        '\nCurrent session will be terminated and you will lose the conversation history.\n\nContinue?',
                        ['Yes, proceed', 'No, dismiss'],
                    )
                    == 0
                )

                if not new_session_requested:
                    continue

                event_stream.add_event(
                    ChangeAgentStateAction(AgentState.STOPPED),
                    EventSource.ENVIRONMENT,
                )

                display_shutdown_message(usage_metrics, sid)
                return
            elif next_message == '/settings':
                display_settings(config)
                modify_settings = cli_confirm(
                    'Which settings would you like to modify?',
                    [
                        'Basic',
                        'Advanced',
                        'Go back',
                    ],
                )

                if modify_settings == 0:
                    new_session_requested = await modify_llm_settings_basic(
                        config, settings_store
                    )
                elif modify_settings == 1:
                    new_session_requested = await modify_llm_settings_advanced(
                        config, settings_store
                    )

                if new_session_requested:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.STOPPED),
                        EventSource.ENVIRONMENT,
                    )
                    display_shutdown_message(usage_metrics, sid)
                    return

                continue

            action = MessageAction(content=next_message)
            event_stream.add_event(action, EventSource.USER)
            return

    async def on_event_async(event: Event) -> None:
        nonlocal reload_microagents
        display_event(event, config)
        update_usage_metrics(event, usage_metrics)

        if isinstance(event, AgentStateChangedObservation):
            if event.agent_state in [
                AgentState.AWAITING_USER_INPUT,
                AgentState.FINISHED,
            ]:
                # Reload microagents after initialization of repo.md
                if reload_microagents:
                    microagents: list[BaseMicroagent] = (
                        runtime.get_microagents_from_selected_repo(None)
                    )
                    memory.load_user_workspace_microagents(microagents)
                    reload_microagents = False
                await prompt_for_next_task()

            if event.agent_state == AgentState.AWAITING_USER_CONFIRMATION:
                user_confirmed = await read_confirmation_input()
                if user_confirmed:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_CONFIRMED),
                        EventSource.USER,
                    )
                else:
                    event_stream.add_event(
                        ChangeAgentStateAction(AgentState.USER_REJECTED),
                        EventSource.USER,
                    )

    def on_event(event: Event) -> None:
        loop.create_task(on_event_async(event))

    event_stream.subscribe(EventStreamSubscriber.MAIN, on_event, str(uuid4()))

    await runtime.connect()

    # Initialize repository if needed
    repo_directory = None
    if config.sandbox.selected_repo:
        repo_directory = initialize_repository_for_runtime(
            runtime,
            selected_repository=config.sandbox.selected_repo,
        )

    # when memory is created, it will load the microagents from the selected repository
    memory = create_memory(
        runtime=runtime,
        event_stream=event_stream,
        sid=sid,
        selected_repository=config.sandbox.selected_repo,
        repo_directory=repo_directory,
    )

    # Clear loading animation
    is_loaded.set()

    # Clear the terminal
    clear()

    # Show OpenHands banner and session ID
    display_banner(session_id=sid, is_loaded=is_loaded)

    # Show OpenHands welcome
    display_welcome_message()

    if initial_user_action:
        # If there's an initial user action, enqueue it and do not prompt again
        event_stream.add_event(initial_user_action, EventSource.USER)
    else:
        # Otherwise prompt for the user's first message right away
        asyncio.create_task(prompt_for_next_task())

    await run_agent_until_done(
        controller, runtime, memory, [AgentState.STOPPED, AgentState.ERROR]
    )

    await cleanup_session(loop, agent, runtime, controller)

    return new_session_requested


async def main(loop: asyncio.AbstractEventLoop):
    """Runs the agent in CLI mode."""

    args = parse_arguments()

    logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: AppConfig = setup_config_from_args(args)

    # Load settings from Settings Store
    # TODO: Make this generic?
    settings_store = await FileSettingsStore.get_instance(config=config, user_id=None)
    settings = await settings_store.load()

    # Use settings from settings store if available and override with command line arguments
    if settings:
        config.default_agent = args.agent_cls if args.agent_cls else settings.agent
        if not args.llm_config and settings.llm_model and settings.llm_api_key:
            llm_config = config.get_llm_config()
            llm_config.model = settings.llm_model
            llm_config.api_key = settings.llm_api_key
            llm_config.base_url = settings.llm_base_url
            config.set_llm_config(llm_config)
        config.security.confirmation_mode = (
            settings.confirmation_mode if settings.confirmation_mode else False
        )

        if settings.enable_default_condenser:
            # TODO: Make this generic?
            llm_config = config.get_llm_config()
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = LLMSummarizingCondenserConfig(
                llm_config=llm_config,
                type='llm',
            )
            config.set_agent_config(agent_config)
            config.enable_default_condenser = True
        else:
            agent_config = config.get_agent_config(config.default_agent)
            agent_config.condenser = NoOpCondenserConfig(type='noop')
            config.set_agent_config(agent_config)
            config.enable_default_condenser = False

    # TODO: Set working directory from config or use current working directory?
    current_dir = config.workspace_base

    if not current_dir:
        raise ValueError('Workspace base directory not specified')

    if not check_folder_security_agreement(current_dir):
        # User rejected, exit application
        return

    # Read task from file, CLI args, or stdin
    task_str = read_task(args, config.cli_multiline_input)

    # If we have a task, create initial user action
    initial_user_action = MessageAction(content=task_str) if task_str else None

    # Run the first session
    new_session_requested = await run_session(
        loop, config, settings_store, current_dir, initial_user_action
    )

    # If a new session was requested, run it
    while new_session_requested:
        new_session_requested = await run_session(
            loop, config, settings_store, current_dir, None
        )


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main(loop))
    except KeyboardInterrupt:
        print('Received keyboard interrupt, shutting down...')
    except ConnectionRefusedError as e:
        print(f'Connection refused: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'An error occurred: {e}')
        sys.exit(1)
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for all tasks to complete with a timeout
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f'Error during cleanup: {e}')
            sys.exit(1)
