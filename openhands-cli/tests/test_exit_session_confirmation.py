#!/usr/bin/env python3
"""
Tests for exit_session_confirmation functionality in OpenHands CLI.
"""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest
from openhands_cli.user_actions import (
    exit_session,
    exit_session_confirmation,
    utils,
)
from openhands_cli.user_actions.types import UserConfirmation
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output.defaults import DummyOutput

from tests.utils import _send_keys

QUESTION = 'Terminate session?'
OPTIONS = ['Yes, proceed', 'No, dismiss']


@pytest.fixture()
def confirm_patch() -> Iterator[MagicMock]:
    """Patch cli_confirm once per test and yield the mock."""
    with patch('openhands_cli.user_actions.exit_session.cli_confirm') as m:
        yield m


def _assert_called_once_with_defaults(mock_cli_confirm: MagicMock) -> None:
    """Ensure the question/options are correct and 'escapable' is not enabled."""
    mock_cli_confirm.assert_called_once()
    args, kwargs = mock_cli_confirm.call_args
    # Positional args
    assert args == (QUESTION, OPTIONS)
    # Should not opt into escapable mode
    assert 'escapable' not in kwargs or kwargs['escapable'] is False


class TestExitSessionConfirmation:
    """Test suite for exit_session_confirmation functionality."""

    @pytest.mark.parametrize(
        'index,expected',
        [
            (0, UserConfirmation.ACCEPT),  # Yes
            (1, UserConfirmation.REJECT),  # No
            (999, UserConfirmation.REJECT),  # Invalid => default reject
            (-1, UserConfirmation.REJECT),  # Negative => default reject
        ],
    )
    def test_index_mapping(
        self, confirm_patch: MagicMock, index: int, expected: UserConfirmation
    ) -> None:
        """All index-to-result mappings, including invalid/negative, in one place."""
        confirm_patch.return_value = index

        result = exit_session_confirmation()

        assert isinstance(result, UserConfirmation)
        assert result == expected
        _assert_called_once_with_defaults(confirm_patch)

    def test_exit_session_confirmation_non_escapable_e2e(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """E2E: non-escapable should ignore Ctrl-C/Ctrl-P/Esc; only Enter returns."""
        real_cli_confirm = utils.cli_confirm

        with create_pipe_input() as pipe:
            output = DummyOutput()

            def wrapper(
                question: str,
                choices: list[str] | None = None,
                initial_selection: int = 0,
                escapable: bool = False,
                **extra: object,
            ) -> int:
                # keep original params; inject test IO
                return real_cli_confirm(
                    question=question,
                    choices=choices,
                    initial_selection=initial_selection,
                    escapable=escapable,
                    input=pipe,
                    output=output,
                )

            # Patch the symbol the caller uses
            monkeypatch.setattr(exit_session, 'cli_confirm', wrapper, raising=True)

            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(exit_session_confirmation)

                _send_keys(pipe, '\x03')  # Ctrl-C (ignored)
                _send_keys(pipe, '\x10')  # Ctrl-P (ignored)
                _send_keys(pipe, '\x1b')  # Esc   (ignored)

                _send_keys(pipe, '\x1b[B')  # Arrow Down to "No, dismiss"
                _send_keys(pipe, '\r')  # Enter

                result = fut.result(timeout=2.0)
                assert result == UserConfirmation.REJECT
