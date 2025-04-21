from typing import List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style

import openhands.agenthub  # noqa F401 (we import this to get the agents registered)
from openhands.core.cli_display import COLOR_GOLD, COMMANDS, DEFAULT_STYLE

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
