import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import toml
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.application import Application
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import clear, print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands import __version__
from openhands.core.config import (
    AppConfig,
    parse_arguments,
    setup_config_from_args,
)
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
    ActionConfirmationStatus,
    ChangeAgentStateAction,
    CmdRunAction,
    FileEditAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    AgentStateChangedObservation,
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
)
from openhands.io import read_task
from openhands.llm.metrics import Metrics
from openhands.mcp import fetch_mcp_tools_from_config
from openhands.microagent.microagent import BaseMicroagent

# Color and styling constants
COLOR_GOLD = '#FFD700'
COLOR_GREY = '#808080'
DEFAULT_STYLE = Style.from_dict(
    {
        'gold': COLOR_GOLD,
        'grey': COLOR_GREY,
        'prompt': f'{COLOR_GOLD} bold',
    }
)

COMMANDS = {
    '/exit': 'Exit the application',
    '/help': 'Display available commands',
    '/init': 'Initialize a new repository',
}

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


class UsageMetrics:
    def __init__(self):
        self.total_cost: float = 0.00
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read: int = 0
        self.total_cache_write: int = 0


prompt_session = PromptSession(style=DEFAULT_STYLE, completer=CommandCompleter())


def display_message(message: str):
    message = message.strip()

    if message:
        print_formatted_text(f'\n{message}\n')


def display_command(command: str):
    container = Frame(
        TextArea(
            text=command,
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Command Run',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_confirmation(confirmation_state: ActionConfirmationStatus):
    status_map = {
        ActionConfirmationStatus.CONFIRMED: ('ansigreen', '✅'),
        ActionConfirmationStatus.REJECTED: ('ansired', '❌'),
        ActionConfirmationStatus.AWAITING_CONFIRMATION: ('ansiyellow', '⏳'),
    }
    color, icon = status_map.get(confirmation_state, ('ansiyellow', ''))

    print_formatted_text(
        FormattedText(
            [
                (color, f'{icon} '),
                (color, str(confirmation_state)),
                ('', '\n'),
            ]
        )
    )


def display_command_output(output: str):
    lines = output.split('\n')
    formatted_lines = []
    for line in lines:
        if line.startswith('[Python Interpreter') or line.startswith('openhands@'):
            # TODO: clean this up once we clean up terminal output
            continue
        formatted_lines.append(line)
        formatted_lines.append('\n')

    # Remove the last newline if it exists
    if formatted_lines:
        formatted_lines.pop()

    container = Frame(
        TextArea(
            text=''.join(formatted_lines),
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Command Output',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_file_edit(event: FileEditAction | FileEditObservation):
    container = Frame(
        TextArea(
            text=f'{event}',
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='File Edit',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_file_read(event: FileReadObservation):
    container = Frame(
        TextArea(
            text=f'{event}',
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='File Read',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text('')


def display_event(event: Event, config: AppConfig) -> None:
    if isinstance(event, Action):
        if hasattr(event, 'thought'):
            display_message(event.thought)
    if isinstance(event, MessageAction):
        if event.source == EventSource.AGENT:
            display_message(event.content)
    if isinstance(event, CmdRunAction):
        display_command(event.command)
    if isinstance(event, CmdOutputObservation):
        display_command_output(event.content)
    if isinstance(event, FileEditAction):
        display_file_edit(event)
    if isinstance(event, FileEditObservation):
        display_file_edit(event)
    if isinstance(event, FileReadObservation):
        display_file_read(event)
    if hasattr(event, 'confirmation_state') and config.security.confirmation_mode:
        display_confirmation(event.confirmation_state)


def display_help(style=DEFAULT_STYLE):
    print_formatted_text(
        HTML(f'\n<grey>OpenHands CLI v{__version__}</grey>\n'), style=style
    )

    print_formatted_text(
        HTML(
            '<gold>OpenHands CLI lets you interact with the OpenHands agent from the command line.</gold>'
        )
    )
    print_formatted_text('')

    print_formatted_text('Things that you can try:')
    print_formatted_text(
        HTML('• Ask questions about the codebase <grey>> How does main.py work?</grey>')
    )
    print_formatted_text(
        HTML(
            '• Edit files or add new features <grey>> Add a new function to ...</grey>'
        )
    )
    print_formatted_text(
        HTML('• Find and fix issues <grey>> Fix the type error in ...</grey>')
    )
    print_formatted_text('')

    print_formatted_text('Some tips to get the most out of OpenHands:')
    print_formatted_text(
        '• Be as specific as possible about the desired outcome or the problem to be solved.'
    )
    print_formatted_text(
        '• Provide context, including relevant file paths and line numbers if available.'
    )
    print_formatted_text('• Break large tasks into smaller, manageable prompts.')
    print_formatted_text('• Include relevant error messages or logs.')
    print_formatted_text(
        '• Specify the programming language or framework, if not obvious.'
    )
    print_formatted_text('')

    print_formatted_text(HTML('Interactive commands:'), style=style)
    for command, description in COMMANDS.items():
        print_formatted_text(
            HTML(f'<gold><b>{command}</b></gold> - <grey>{description}</grey>'),
            style=style,
        )
    print_formatted_text('')
    print_formatted_text(
        HTML(
            '<grey>Learn more at: https://docs.all-hands.dev/modules/usage/getting-started</grey>'
        )
    )
    print_formatted_text('')


def display_banner(session_id: str, is_loaded: asyncio.Event):
    print_formatted_text(
        HTML(r"""<gold>
     ___                    _   _                 _
    /  _ \ _ __   ___ _ __ | | | | __ _ _ __   __| |___
    | | | | '_ \ / _ \ '_ \| |_| |/ _` | '_ \ / _` / __|
    | |_| | |_) |  __/ | | |  _  | (_| | | | | (_| \__ \
    \___ /| .__/ \___|_| |_|_| |_|\__,_|_| |_|\__,_|___/
          |_|
    </gold>"""),
        style=DEFAULT_STYLE,
    )

    print_formatted_text(HTML(f'<grey>OpenHands CLI v{__version__}</grey>'))

    banner_text = (
        'Initialized session' if is_loaded.is_set() else 'Initializing session'
    )
    print_formatted_text(HTML(f'\n<grey>{banner_text} {session_id}</grey>\n'))


def display_welcome_message():
    print_formatted_text(
        HTML("<gold>Let's start building!</gold>\n"), style=DEFAULT_STYLE
    )
    print_formatted_text(
        HTML('What do you want to build? <grey>Type /help for help</grey>\n'),
        style=DEFAULT_STYLE,
    )


def display_initialization_animation(text, is_loaded: asyncio.Event):
    ANIMATION_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    i = 0
    while not is_loaded.is_set():
        sys.stdout.write('\n')
        sys.stdout.write(
            f'\033[s\033[J\033[38;2;255;215;0m[{ANIMATION_FRAMES[i % len(ANIMATION_FRAMES)]}] {text}\033[0m\033[u\033[1A'
        )
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

    sys.stdout.write('\r' + ' ' * (len(text) + 10) + '\r')
    sys.stdout.flush()


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
    except KeyboardInterrupt:
        return '/exit'
    except EOFError:
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

            init_repo = cli_confirm(
                'Do you want to re-initialize?',
                ['Yes, re-initialize', 'No, dismiss'],
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

        init_repo = cli_confirm(
            'Do you want to proceed?',
            ['Yes, create', 'No, dismiss'],
        )

    return init_repo


def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def write_to_file(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)


def cli_confirm(question: str = 'Are you sure?', choices: Optional[List[str]] = None):
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
        event.app.exit(result=selected[0] == 0)

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
    """Updates the UsageMetrics object with data from an event's llm_metrics."""
    if hasattr(event, 'llm_metrics'):
        llm_metrics: Metrics | None = getattr(event, 'llm_metrics', None)
        if llm_metrics:
            # Safely get accumulated_cost
            cost = getattr(llm_metrics, 'accumulated_cost', 0)
            # Ensure cost is a number before adding
            usage_metrics.total_cost += cost if isinstance(cost, float) else 0

            # Safely get token usage details object/dict
            token_usage = getattr(llm_metrics, 'accumulated_token_usage', None)
            if token_usage:
                # Assume object access using getattr, providing defaults
                prompt_tokens = getattr(token_usage, 'prompt_tokens', 0)
                completion_tokens = getattr(token_usage, 'completion_tokens', 0)
                cache_read = getattr(token_usage, 'cache_read_tokens', 0)
                cache_write = getattr(token_usage, 'cache_write_tokens', 0)

                # Ensure tokens are numbers before adding
                usage_metrics.total_input_tokens += (
                    prompt_tokens if isinstance(prompt_tokens, int) else 0
                )
                usage_metrics.total_output_tokens += (
                    completion_tokens if isinstance(completion_tokens, int) else 0
                )
                usage_metrics.total_cache_read += (
                    cache_read if isinstance(cache_read, int) else 0
                )
                usage_metrics.total_cache_write += (
                    cache_write if isinstance(cache_write, int) else 0
                )


def shutdown(usage_metrics: UsageMetrics, session_id: str):
    cost_str = f'${usage_metrics.total_cost:.6f}'
    input_tokens_str = f'{usage_metrics.total_input_tokens:,}'
    cache_read_str = f'{usage_metrics.total_cache_read:,}'
    cache_write_str = f'{usage_metrics.total_cache_write:,}'
    output_tokens_str = f'{usage_metrics.total_output_tokens:,}'
    total_tokens_str = (
        f'{usage_metrics.total_input_tokens + usage_metrics.total_output_tokens:,}'
    )

    labels_and_values = [
        ('   Total Cost (USD):', cost_str),
        ('   Total Input Tokens:', input_tokens_str),
        ('      Cache Hits:', cache_read_str),
        ('      Cache Writes:', cache_write_str),
        ('   Total Output Tokens:', output_tokens_str),
        ('   Total Tokens:', total_tokens_str),
    ]

    # Calculate max widths for alignment
    max_label_width = max(len(label) for label, _ in labels_and_values)
    max_value_width = max(len(value) for _, value in labels_and_values)

    # Construct the summary text with aligned columns
    summary_lines = [
        f'{label:<{max_label_width}} {value:>{max_value_width}}'
        for label, value in labels_and_values
    ]
    summary_text = '\n'.join(summary_lines)

    container = Frame(
        TextArea(
            text=summary_text,
            read_only=True,
            style=COLOR_GREY,
            wrap_lines=True,
        ),
        title='Session Summary',
        style=f'fg:{COLOR_GREY}',
    )
    print_container(container)
    print_formatted_text(HTML(f'\n<grey>Closed session {session_id}</grey>\n'))


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
                    f'Do you trust the files in this folder?\n\n'
                    f'{current_dir}\n\n'
                    'OpenHands may read and execute files in this folder with your permission.'
                ),
                style=COLOR_GREY,
                read_only=True,
                wrap_lines=True,
            ),
            style=f'fg:{COLOR_GREY}',
        )

        clear()
        print_container(security_frame)

        confirm = cli_confirm('Do you wish to continue?', ['Yes, proceed', 'No, exit'])

        if confirm:
            manage_openhands_file(current_dir, add_to_trusted=True)

        return confirm

    return True


async def main(loop: asyncio.AbstractEventLoop):
    """Runs the agent in CLI mode."""

    reload_microagents = False

    args = parse_arguments()

    logger.setLevel(logging.WARNING)

    # Load config from toml and override with command line arguments
    config: AppConfig = setup_config_from_args(args)

    # TODO: Set working directory from config or use current working directory?
    current_dir = config.workspace_base

    if not current_dir:
        raise ValueError('Workspace base directory not specified')

    # Read task from file, CLI args, or stdin
    task_str = read_task(args, config.cli_multiline_input)

    # If we have a task, create initial user action
    initial_user_action = MessageAction(content=task_str) if task_str else None

    sid = str(uuid4())
    is_loaded = asyncio.Event()

    # Show OpenHands banner and session ID
    display_banner(session_id=sid, is_loaded=is_loaded)

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
        nonlocal reload_microagents
        while True:
            next_message = await read_prompt_input(config.cli_multiline_input)

            if not next_message.strip():
                continue

            if next_message == '/exit':
                event_stream.add_event(
                    ChangeAgentStateAction(AgentState.STOPPED), EventSource.ENVIRONMENT
                )
                shutdown(usage_metrics, sid)
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

    if not check_folder_security_agreement(current_dir):
        # User rejected, exit application
        return

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
