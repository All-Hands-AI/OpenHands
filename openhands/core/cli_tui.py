# CLI TUI input and output functions
# Handles all input and output to the console
# CLI Settings are handled separately in cli_settings.py

import asyncio
import sys
import time

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.application import Application
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, FormattedText, StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.patch_stdout import patch_stdout
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
from openhands.llm.metrics import Metrics

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
        self.metrics: Metrics = Metrics()
        self.session_init_time: float = time.time()


class CustomDiffLexer(Lexer):
    """Custom lexer for the specific diff format."""

    def lex_document(self, document) -> StyleAndTextTuples:
        lines = document.lines

        def get_line(lineno: int) -> StyleAndTextTuples:
            line = lines[lineno]
            if line.startswith('+'):
                return [('ansigreen', line)]
            elif line.startswith('-'):
                return [('ansired', line)]
            elif line.startswith('[') or line.startswith('('):
                # Style for metadata lines like [Existing file...] or (content...)
                return [('bold', line)]
            else:
                # Default style for other lines
                return [('', line)]

        return get_line


# CLI initialization and startup display functions
def display_runtime_initialization_message(runtime: str):
    print_formatted_text('')
    if runtime == 'local':
        print_formatted_text(HTML('<grey>⚙️ Starting local runtime...</grey>'))
    elif runtime == 'docker':
        print_formatted_text(HTML('<grey>🐳 Starting Docker runtime...</grey>'))
    print_formatted_text('')


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
    print_formatted_text('')
    print_formatted_text(HTML(f'<grey>{banner_text} {session_id}</grey>'))
    print_formatted_text('')


def display_welcome_message():
    print_formatted_text(
        HTML("<gold>Let's start building!</gold>\n"), style=DEFAULT_STYLE
    )
    print_formatted_text(
        HTML('What do you want to build? <grey>Type /help for help</grey>'),
        style=DEFAULT_STYLE,
    )


def display_initial_user_prompt(prompt: str):
    print_formatted_text(
        FormattedText(
            [
                ('', '\n'),
                (COLOR_GOLD, '> '),
                ('', prompt),
            ]
        )
    )


# Prompt output display functions
def display_event(event: Event, config: AppConfig) -> None:
    if isinstance(event, Action):
        if hasattr(event, 'thought'):
            display_message(event.thought)
    if isinstance(event, MessageAction):
        if event.source == EventSource.AGENT:
            display_message(event.content)
    if isinstance(event, CmdRunAction):
        display_command(event)
    if isinstance(event, CmdOutputObservation):
        display_command_output(event.content)
    if isinstance(event, FileEditAction):
        display_file_edit(event)
    if isinstance(event, FileEditObservation):
        display_file_edit(event)
    if isinstance(event, FileReadObservation):
        display_file_read(event)


def display_message(message: str):
    time.sleep(0.2)
    message = message.strip()

    if message:
        print_formatted_text(f'\n{message}')


def display_command(event: CmdRunAction):
    if event.confirmation_state == ActionConfirmationStatus.AWAITING_CONFIRMATION:
        container = Frame(
            TextArea(
                text=f'$ {event.command}',
                read_only=True,
                style=COLOR_GREY,
                wrap_lines=True,
            ),
            title='Action',
            style='ansired',
        )
        print_formatted_text('')
        print_container(container)


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
        title='Action Output',
        style=f'fg:{COLOR_GREY}',
    )
    print_formatted_text('')
    print_container(container)


def display_file_edit(event: FileEditAction | FileEditObservation):
    if isinstance(event, FileEditObservation):
        container = Frame(
            TextArea(
                text=event.visualize_diff(n_context_lines=4),
                read_only=True,
                wrap_lines=True,
                lexer=CustomDiffLexer(),
            ),
            title='File Edit',
            style=f'fg:{COLOR_GREY}',
        )
        print_container(container)


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


# Interactive command output display functions
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
            '<grey>Learn more at: https://docs.all-hands.dev/modules/usage/getting-started</grey>'
        )
    )


def display_usage_metrics(usage_metrics: UsageMetrics):
    cost_str = f'${usage_metrics.metrics.accumulated_cost:.6f}'
    input_tokens_str = (
        f'{usage_metrics.metrics.accumulated_token_usage.prompt_tokens:,}'
    )
    cache_read_str = (
        f'{usage_metrics.metrics.accumulated_token_usage.cache_read_tokens:,}'
    )
    cache_write_str = (
        f'{usage_metrics.metrics.accumulated_token_usage.cache_write_tokens:,}'
    )
    output_tokens_str = (
        f'{usage_metrics.metrics.accumulated_token_usage.completion_tokens:,}'
    )
    total_tokens_str = f'{usage_metrics.metrics.accumulated_token_usage.prompt_tokens + usage_metrics.metrics.accumulated_token_usage.completion_tokens:,}'

    labels_and_values = [
        ('   Total Cost (USD):', cost_str),
        ('', ''),
        ('   Total Input Tokens:', input_tokens_str),
        ('      Cache Hits:', cache_read_str),
        ('      Cache Writes:', cache_write_str),
        ('   Total Output Tokens:', output_tokens_str),
        ('', ''),
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

    print_container(container)


def get_session_duration(session_init_time: float) -> str:
    current_time = time.time()
    session_duration = current_time - session_init_time
    hours, remainder = divmod(session_duration, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{int(hours)}h {int(minutes)}m {int(seconds)}s'


def display_shutdown_message(usage_metrics: UsageMetrics, session_id: str):
    duration_str = get_session_duration(usage_metrics.session_init_time)

    print_formatted_text(HTML('<grey>Closing current session...</grey>'))
    print_formatted_text('')
    display_usage_metrics(usage_metrics)
    print_formatted_text('')
    print_formatted_text(HTML(f'<grey>Session duration: {duration_str}</grey>'))
    print_formatted_text('')
    print_formatted_text(HTML(f'<grey>Closed session {session_id}</grey>'))
    print_formatted_text('')


def display_status(usage_metrics: UsageMetrics, session_id: str):
    duration_str = get_session_duration(usage_metrics.session_init_time)

    print_formatted_text('')
    print_formatted_text(HTML(f'<grey>Session ID: {session_id}</grey>'))
    print_formatted_text(HTML(f'<grey>Uptime:     {duration_str}</grey>'))
    print_formatted_text('')
    display_usage_metrics(usage_metrics)


# Common input functions
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


prompt_session = PromptSession(style=DEFAULT_STYLE)

# RPrompt animation related variables
SPINNER_FRAMES = [
    '[ ■□□□ ]',
    '[ □■□□ ]',
    '[ □□■□ ]',
    '[ □□□■ ]',
    '[ □□■□ ]',
    '[ □■□□ ]',
]
ANIMATION_INTERVAL = 0.2  # seconds

current_frame_index = 0
last_update_time = time.monotonic()


# RPrompt function for the user confirmation
def get_rprompt() -> FormattedText:
    """
    Returns the current animation frame for the rprompt.
    This function is called by prompt_toolkit during rendering.
    """
    global current_frame_index, last_update_time

    # Only update the frame if enough time has passed
    # This prevents excessive recalculation during rendering
    now = time.monotonic()
    if now - last_update_time > ANIMATION_INTERVAL:
        current_frame_index = (current_frame_index + 1) % len(SPINNER_FRAMES)
        last_update_time = now

    # Return the frame wrapped in FormattedText
    return FormattedText(
        [
            ('', ' '),  # Add a space before the spinner
            (COLOR_GOLD, SPINNER_FRAMES[current_frame_index]),
        ]
    )


async def read_prompt_input(multiline=False):
    try:
        if multiline:
            kb = KeyBindings()

            @kb.add('c-d')
            def _(event):
                event.current_buffer.validate_and_handle()

            with patch_stdout():
                print_formatted_text('')
                message = await prompt_session.prompt_async(
                    'Enter your message and press Ctrl+D to finish:\n',
                    multiline=True,
                    key_bindings=kb,
                )
        else:
            with patch_stdout():
                print_formatted_text('')
                prompt_session.completer = CommandCompleter()
                message = await prompt_session.prompt_async(
                    '> ',
                )
        return message
    except (KeyboardInterrupt, EOFError):
        return '/exit'


async def read_confirmation_input():
    try:
        with patch_stdout():
            prompt_session.completer = None
            confirmation = await prompt_session.prompt_async(
                'Proceed with action? (y)es/(n)o > ',
                rprompt=get_rprompt,
                refresh_interval=ANIMATION_INTERVAL / 2,
            )
            prompt_session.rprompt = None
            confirmation = confirmation.strip().lower()
            return confirmation in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        return False


def cli_confirm(
    question: str = 'Are you sure?', choices: list[str] | None = None
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


def kb_cancel():
    """Custom key bindings to handle ESC as a user cancellation."""
    bindings = KeyBindings()

    @bindings.add('escape')
    def _(event):
        event.app.exit(exception=UserCancelledError, style='class:aborting')

    return bindings


class UserCancelledError(Exception):
    """Raised when the user cancels an operation via key binding."""

    pass
