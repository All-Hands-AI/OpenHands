import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import pytest
from openhands_cli.user_actions.utils import get_session_prompter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput

from tests.utils import _send_keys


def _run_prompt_and_type(
    prompt_text: str,
    keys: str,
    *,
    expect_exception: Optional[type[BaseException]] = None,
    timeout: float = 2.0,
    settle: float = 0.05,
) -> str | None:
    """
    Helper to:
      1) create a pipe + session,
      2) start session.prompt in a background thread,
      3) send keys, and
      4) return the result or raise the expected exception.

    Returns:
      - The prompt result (str) if no exception expected.
      - None if an exception is expected and raised.
    """
    with create_pipe_input() as pipe:
        session = get_session_prompter(input=pipe, output=DummyOutput())
        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(session.prompt, HTML(prompt_text))
            # Allow the prompt loop to start consuming input
            time.sleep(settle)
            _send_keys(pipe, keys)
            if expect_exception:
                with pytest.raises(expect_exception):
                    fut.result(timeout=timeout)
                return None
            return fut.result(timeout=timeout)


@pytest.mark.parametrize(
    'desc,keys,expected',
    [
        ('basic single line', 'hello world\r', 'hello world'),
        ('empty input', '\r', ''),
        (
            'single multiline via backslash-enter',
            'line 1\\\rline 2\r',
            'line 1\nline 2',
        ),
        (
            'multiple multiline segments',
            'first line\\\rsecond line\\\rthird line\r',
            'first line\nsecond line\nthird line',
        ),
        (
            'backslash-only newline then text',
            '\\\rafter newline\r',
            '\nafter newline',
        ),
        (
            'mixed content (code-like)',
            "def function():\\\r    return 'hello'\\\r    # end of function\r",
            "def function():\n    return 'hello'\n    # end of function",
        ),
        (
            'whitespace preservation (including blank line)',
            '  indented line\\\r\\\r    more indented\r',
            '  indented line\n\n    more indented',
        ),
        (
            'special characters',
            'echo \'hello world\'\\\rgrep -n "pattern" file.txt\r',
            'echo \'hello world\'\ngrep -n "pattern" file.txt',
        ),
    ],
)
def test_get_session_prompter_scenarios(desc, keys, expected):
    """Covers most behaviors via parametrization to reduce duplication."""
    result = _run_prompt_and_type('<gold>> </gold>', keys)
    assert result == expected


def test_get_session_prompter_keyboard_interrupt():
    """Focused test for Ctrl+C behavior."""
    _run_prompt_and_type('<gold>> </gold>', '\x03', expect_exception=KeyboardInterrupt)


def test_get_session_prompter_default_parameters():
    """Lightweight sanity check for default construction."""
    session = get_session_prompter()
    assert session is not None
    assert session.multiline is True
    assert session.key_bindings is not None
    assert session.completer is not None

    # Prompt continuation should be callable and return the expected string
    cont = session.prompt_continuation
    assert callable(cont)
    assert cont(80, 1, False) == '...'
