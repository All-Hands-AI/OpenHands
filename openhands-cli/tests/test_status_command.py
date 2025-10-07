"""Simplified tests for the /status command functionality."""

from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch

import pytest

from openhands_cli.tui.status import display_status
from openhands.sdk.llm.utils.metrics import Metrics, TokenUsage


# ---------- Fixtures & helpers ----------

@pytest.fixture
def conversation():
    """Minimal conversation with empty events and pluggable stats."""
    conv = Mock()
    conv.id = uuid4()
    conv.state = Mock(events=[])
    conv.conversation_stats = Mock()
    return conv


def make_metrics(cost=None, usage=None) -> Metrics:
    m = Metrics()
    if cost is not None:
        m.accumulated_cost = cost
    m.accumulated_token_usage = usage
    return m


def call_display_status(conversation, session_start):
    """Call display_status with prints patched; return (mock_pf, mock_pc, text)."""
    with patch('openhands_cli.tui.status.print_formatted_text') as pf, \
         patch('openhands_cli.tui.status.print_container') as pc:
        display_status(conversation, session_start_time=session_start)
        # First container call; extract the Frame/TextArea text
        container = pc.call_args_list[0][0][0]
        text = getattr(container.body, "text", "")
        return pf, pc, str(text)


# ---------- Tests ----------

def test_display_status_box_title(conversation):
    session_start = datetime.now()
    conversation.conversation_stats.get_combined_metrics.return_value = make_metrics()

    with patch('openhands_cli.tui.status.print_formatted_text') as pf, \
         patch('openhands_cli.tui.status.print_container') as pc:
        display_status(conversation, session_start_time=session_start)

        assert pf.called and pc.called

        container = pc.call_args_list[0][0][0]
        assert hasattr(container, "title")
        assert "Usage Metrics" in container.title


@pytest.mark.parametrize(
    "delta,expected",
    [
        (timedelta(seconds=0), "0h 0m"),
        (timedelta(minutes=5, seconds=30), "5m"),
        (timedelta(hours=1, minutes=30, seconds=45), "1h 30m"),
        (timedelta(hours=2, minutes=15, seconds=30), "2h 15m"),
    ],
)
def test_display_status_uptime(conversation, delta, expected):
    session_start = datetime.now() - delta
    conversation.conversation_stats.get_combined_metrics.return_value = make_metrics()

    with patch('openhands_cli.tui.status.print_formatted_text') as pf, \
         patch('openhands_cli.tui.status.print_container'):
        display_status(conversation, session_start_time=session_start)
        # uptime is printed in the 2nd print_formatted_text call
        uptime_call_str = str(pf.call_args_list[1])
        assert expected in uptime_call_str
        # conversation id appears in the first print call
        id_call_str = str(pf.call_args_list[0])
        assert str(conversation.id) in id_call_str


@pytest.mark.parametrize(
    "cost,usage,expecteds",
    [
        # Empty/zero case
        (None, None, ["$0.000000", "0", "0", "0", "0", "0"]),
        # Only cost, usage=None
        (0.05, None, ["$0.050000", "0", "0", "0", "0", "0"]),
        # Full metrics
        (
            0.123456,
            TokenUsage(
                prompt_tokens=1500,
                completion_tokens=800,
                cache_read_tokens=200,
                cache_write_tokens=100,
            ),
            ["$0.123456", "1,500", "800", "200", "100", "2,300"],
        ),
        # Larger numbers (comprehensive)
        (
            1.234567,
            TokenUsage(
                prompt_tokens=5000,
                completion_tokens=3000,
                cache_read_tokens=500,
                cache_write_tokens=250,
            ),
            ["$1.234567", "5,000", "3,000", "500", "250", "8,000"],
        ),
    ],
)
def test_display_status_metrics(conversation, cost, usage, expecteds):
    session_start = datetime.now()
    conversation.conversation_stats.get_combined_metrics.return_value = make_metrics(cost, usage)

    pf, pc, text = call_display_status(conversation, session_start)

    assert pf.called and pc.called
    for expected in expecteds:
        assert expected in text
