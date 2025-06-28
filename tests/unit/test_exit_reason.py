import time
from unittest.mock import MagicMock

import pytest

from openhands.cli.commands import handle_commands
from openhands.core.schema.exit_reason import ExitReason


def test_exit_reason_enum_values():
    assert ExitReason.INTENTIONAL.value == 'intentional'
    assert ExitReason.INTERRUPTED.value == 'interrupted'
    assert ExitReason.ERROR.value == 'error'


def test_exit_reason_enum_names():
    assert ExitReason['INTENTIONAL'] == ExitReason.INTENTIONAL
    assert ExitReason['INTERRUPTED'] == ExitReason.INTERRUPTED
    assert ExitReason['ERROR'] == ExitReason.ERROR


def test_exit_reason_str_representation():
    assert str(ExitReason.INTENTIONAL) == 'ExitReason.INTENTIONAL'
    assert repr(ExitReason.ERROR) == "<ExitReason.ERROR: 'error'>"


@pytest.mark.asyncio
async def test_handle_exit_command_returns_intentional(monkeypatch):
    monkeypatch.setattr('openhands.cli.commands.cli_confirm', lambda *a, **k: 0)

    mock_usage_metrics = MagicMock()
    mock_usage_metrics.session_init_time = time.time() - 3600
    mock_usage_metrics.metrics.accumulated_cost = 0.123456

    # Mock all token counts used in display formatting
    mock_usage_metrics.metrics.accumulated_token_usage.prompt_tokens = 1234
    mock_usage_metrics.metrics.accumulated_token_usage.cache_read_tokens = 5678
    mock_usage_metrics.metrics.accumulated_token_usage.cache_write_tokens = 9012
    mock_usage_metrics.metrics.accumulated_token_usage.completion_tokens = 3456

    (
        close_repl,
        reload_microagents,
        new_session_requested,
        exit_reason,
    ) = await handle_commands(
        '/exit',
        MagicMock(),
        mock_usage_metrics,
        'test-session',
        MagicMock(),
        '/tmp/test',
        MagicMock(),
    )

    assert exit_reason == ExitReason.INTENTIONAL
