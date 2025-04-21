import asyncio
import sys
import time

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.shortcuts import print_container
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea

from openhands import __version__
from openhands.core.config import AppConfig
from openhands.events import EventSource
from openhands.events.action import (
    Action,
    ActionConfirmationStatus,
    CmdRunAction,
    FileEditAction,
    MessageAction,
)
from openhands.events.event import Event
from openhands.events.observation import (
    CmdOutputObservation,
    FileEditObservation,
    FileReadObservation,
)

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
    '/status': 'Display session details and usage metrics',
    '/new': 'Create a new session',
    '/settings': 'Display and modify current settings',
}


class UsageMetrics:
    def __init__(self):
        self.total_cost: float = 0.00
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read: int = 0
        self.total_cache_write: int = 0
        self.session_init_time: float = time.time()


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


def display_help():
    # Version header and introduction
    print_formatted_text(
        HTML(
            f'\n<grey>OpenHands CLI v{__version__}</grey>\n'
            '<gold>OpenHands CLI lets you interact with the OpenHands agent from the command line.</gold>\n'
        )
    )

    # Usage examples
    print_formatted_text('Things that you can try:')
    print_formatted_text(
        HTML(
            '• Ask questions about the codebase <grey>> How does main.py work?</grey>\n'
            '• Edit files or add new features <grey>> Add a new function to ...</grey>\n'
            '• Find and fix issues <grey>> Fix the type error in ...</grey>\n'
        )
    )

    # Tips section
    print_formatted_text(
        'Some tips to get the most out of OpenHands:\n'
        '• Be as specific as possible about the desired outcome or the problem to be solved.\n'
        '• Provide context, including relevant file paths and line numbers if available.\n'
        '• Break large tasks into smaller, manageable prompts.\n'
        '• Include relevant error messages or logs.\n'
        '• Specify the programming language or framework, if not obvious.\n'
    )

    # Commands section
    print_formatted_text(HTML('Interactive commands:'))
    commands_html = ''
    for command, description in COMMANDS.items():
        commands_html += f'<gold><b>{command}</b></gold> - <grey>{description}</grey>\n'
    print_formatted_text(HTML(commands_html))

    # Footer
    print_formatted_text(
        HTML(
            '<grey>Learn more at: https://docs.all-hands.dev/modules/usage/getting-started</grey>\n'
        )
    )


def display_runtime_initialization_message(runtime: str):
    print_formatted_text('')
    if runtime == 'local':
        print_formatted_text(
            HTML(
                '<grey>⚙️ Keeping it grounded: local startup sequence initiated...</grey>'
            )
        )
    elif runtime == 'docker':
        print_formatted_text(
            HTML(
                '<grey>🐳 All hands on deck! Preparing Docker launch sequence...</grey>'
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


def display_usage_metrics(usage_metrics: UsageMetrics):
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
        f'{label:<{max_label_width}} {value:<{max_value_width}}'
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
        title='Usage Metrics',
        style=f'fg:{COLOR_GREY}',
    )
    print_formatted_text('')
    print_container(container)
    print_formatted_text('')  # Add a newline after the frame


def display_shutdown_message(usage_metrics: UsageMetrics, session_id: str):
    print_formatted_text(HTML('<grey>Closing current session...</grey>'))
    display_usage_metrics(usage_metrics)
    print_formatted_text(HTML(f'<grey>Closed session {session_id}</grey>\n'))


def display_status(usage_metrics: UsageMetrics, session_id: str):
    current_time = time.time()
    session_duration = current_time - usage_metrics.session_init_time
    hours, remainder = divmod(session_duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_str = f'{int(hours)}h {int(minutes)}m {int(seconds)}s'

    print_formatted_text('')  # Add a newline
    print_formatted_text(HTML(f'<grey>Session ID: {session_id}</grey>'))
    print_formatted_text(HTML(f'<grey>Session Duration: {duration_str}</grey>'))
    display_usage_metrics(usage_metrics)
