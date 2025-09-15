from prompt_toolkit.application import Application
from prompt_toolkit.input.base import Input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output.base import Output
from prompt_toolkit.shortcuts import prompt

from openhands_cli.tui import DEFAULT_STYLE


def build_keybindings(
    choices: list[str], selected: list[int], escapable: bool
) -> KeyBindings:
    """Create keybindings for the confirm UI. Split for testability."""
    kb = KeyBindings()

    @kb.add("up")
    def _handle_up(event: KeyPressEvent) -> None:
        selected[0] = (selected[0] - 1) % len(choices)

    @kb.add("down")
    def _handle_down(event: KeyPressEvent) -> None:
        selected[0] = (selected[0] + 1) % len(choices)

    @kb.add("enter")
    def _handle_enter(event: KeyPressEvent) -> None:
        event.app.exit(result=selected[0])

    if escapable:

        @kb.add("c-c")  # Ctrl+C
        def _handle_hard_interrupt(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt())

        @kb.add("c-p")  # Ctrl+P
        def _handle_pause_interrupt(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt())

        @kb.add("escape")  # Escape key
        def _handle_escape(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt())

    return kb


def build_layout(question: str, choices: list[str], selected_ref: list[int]) -> Layout:
    """Create the layout for the confirm UI. Split for testability."""

    def get_choice_text() -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        lines.append(("class:question", f"{question}\n\n"))
        for i, choice in enumerate(choices):
            is_selected = i == selected_ref[0]
            prefix = "> " if is_selected else "  "
            style = "class:selected" if is_selected else "class:unselected"
            lines.append((style, f"{prefix}{choice}\n"))
        return lines

    content_window = Window(
        FormattedTextControl(get_choice_text),
        always_hide_cursor=True,
        height=Dimension(max=8),
    )
    return Layout(HSplit([content_window]))


def cli_confirm(
    question: str = "Are you sure?",
    choices: list[str] | None = None,
    initial_selection: int = 0,
    escapable: bool = False,
    input: Input | None = None,  # strictly for unit testing
    output: Output | None = None,  # strictly for unit testing
) -> int:
    """Display a confirmation prompt with the given question and choices.

    Returns the index of the selected choice.
    """
    if choices is None:
        choices = ["Yes", "No"]
    selected = [initial_selection]  # Using list to allow modification in closure

    kb = build_keybindings(choices, selected, escapable)
    layout = build_layout(question, choices, selected)

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=DEFAULT_STYLE,
        full_screen=False,
        input=input,
        output=output,
    )

    return int(app.run(in_thread=True))


def prompt_user(question: str) -> tuple[str, bool]:
    """Prompt user to enter a reason for rejecting actions.

    Returns:
        Tuple of (reason, should_defer) where:
        - reason: The reason entered by the user
        - should_defer: True if user pressed Ctrl+C or Ctrl+P, False otherwise
    """

    kb = KeyBindings()

    @kb.add("c-c")
    def _(event: KeyPressEvent) -> None:
        raise KeyboardInterrupt()

    @kb.add("c-p")
    def _(event: KeyPressEvent) -> None:
        raise KeyboardInterrupt()

    try:
        reason = str(
            prompt(
                question,
                style=DEFAULT_STYLE,
                key_bindings=kb,
            )
        )
        return reason.strip(), False
    except KeyboardInterrupt:
        return "", True
