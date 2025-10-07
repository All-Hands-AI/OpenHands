"""Tests for the /status command functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from openhands_cli.agent_chat import _display_status
from openhands.sdk.conversation.state import ConversationStats, Event
from openhands.sdk.llm.utils.metrics import Metrics, TokenUsage


class TestDisplayStatus:
    """Test the _display_status function."""

    def test_display_status_with_empty_conversation(self, capsys):
        """Test status display with a conversation that has no events or stats."""
        # Create a mock conversation with minimal data
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()  # Default empty metrics
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify basic information is displayed
        assert str(mock_conversation.id) in captured.out
        assert "Uptime:          0h 0m 0s" in captured.out
        assert "Usage Metrics" in captured.out
        assert "Total Cost (USD):    $0.000000" in captured.out
        assert "Total Input Tokens:  0" in captured.out
        assert "Total Output Tokens: 0" in captured.out
        assert "Total Tokens:        0" in captured.out

    def test_display_status_with_metrics(self, capsys):
        """Test status display with conversation that has usage metrics."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Create metrics with some usage data
        mock_metrics = Metrics()
        mock_metrics.accumulated_cost = 0.123456
        mock_metrics.accumulated_token_usage = TokenUsage(
            prompt_tokens=1500,
            completion_tokens=800,
            cache_read_tokens=200,
            cache_write_tokens=100
        )
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify metrics are displayed correctly
        assert "Total Cost (USD):    $0.123456" in captured.out
        assert "Total Input Tokens:  1500" in captured.out
        assert "Total Output Tokens: 800" in captured.out
        assert "Cache Hits:       200" in captured.out
        assert "Cache Writes:     100" in captured.out
        assert "Total Tokens:        2300" in captured.out  # 1500 + 800

    def test_display_status_with_uptime_calculation(self, capsys):
        """Test status display with uptime calculation from first event."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        
        # Create a mock event with timestamp from 1 hour, 30 minutes, 45 seconds ago
        past_time = datetime.now() - timedelta(hours=1, minutes=30, seconds=45)
        mock_event = Mock()
        mock_event.timestamp = past_time.isoformat()
        mock_conversation.state.events = [mock_event]
        
        # Mock conversation stats with empty metrics
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify uptime is calculated (should be approximately 1h 30m 45s)
        # We'll check for the hour and minute parts since seconds might vary slightly
        assert "1h 30m" in captured.out

    def test_display_status_with_timezone_timestamp(self, capsys):
        """Test status display with timezone-aware timestamp."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        
        # Create a mock event with timezone-aware timestamp
        past_time = datetime.now() - timedelta(minutes=5, seconds=30)
        mock_event = Mock()
        mock_event.timestamp = past_time.isoformat() + 'Z'  # UTC timezone
        mock_conversation.state.events = [mock_event]
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify uptime is calculated (should be approximately 0h 5m 30s)
        assert "0h 5m" in captured.out

    def test_display_status_with_invalid_timestamp(self, capsys):
        """Test status display handles invalid timestamp gracefully."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        
        # Create a mock event with invalid timestamp
        mock_event = Mock()
        mock_event.timestamp = "invalid-timestamp"
        mock_conversation.state.events = [mock_event]
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify it falls back to default uptime
        assert "Uptime:          0h 0m 0s" in captured.out

    def test_display_status_with_none_token_usage(self, capsys):
        """Test status display handles None token usage gracefully."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Create metrics with None token usage
        mock_metrics = Metrics()
        mock_metrics.accumulated_cost = 0.05
        mock_metrics.accumulated_token_usage = None
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify it handles None token usage gracefully
        assert "Total Cost (USD):    $0.050000" in captured.out
        assert "Total Input Tokens:  0" in captured.out
        assert "Total Output Tokens: 0" in captured.out
        assert "Cache Hits:       0" in captured.out
        assert "Cache Writes:     0" in captured.out
        assert "Total Tokens:        0" in captured.out

    def test_display_status_box_formatting(self, capsys):
        """Test that the status display creates proper box formatting."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify box formatting characters are present
        assert "┌" in captured.out  # Top-left corner
        assert "┐" in captured.out  # Top-right corner
        assert "└" in captured.out  # Bottom-left corner
        assert "┘" in captured.out  # Bottom-right corner
        assert "│" in captured.out  # Vertical borders
        assert "─" in captured.out  # Horizontal borders
        assert "Usage Metrics" in captured.out  # Title in box

    def test_display_status_comprehensive_scenario(self, capsys):
        """Test status display with a comprehensive scenario including all data."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        
        # Create a mock event with timestamp from 2 hours, 15 minutes, 30 seconds ago
        past_time = datetime.now() - timedelta(hours=2, minutes=15, seconds=30)
        mock_event = Mock()
        mock_event.timestamp = past_time.isoformat()
        mock_conversation.state.events = [mock_event]
        
        # Create comprehensive metrics
        mock_metrics = Metrics()
        mock_metrics.accumulated_cost = 1.234567
        mock_metrics.accumulated_token_usage = TokenUsage(
            prompt_tokens=5000,
            completion_tokens=3000,
            cache_read_tokens=500,
            cache_write_tokens=250
        )
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function
        _display_status(mock_conversation, use_formatted_text=False)
        
        # Capture output
        captured = capsys.readouterr()
        
        # Verify all components are present and correct
        assert str(mock_conversation.id) in captured.out
        assert "2h 15m" in captured.out  # Uptime
        assert "Total Cost (USD):    $1.234567" in captured.out
        assert "Total Input Tokens:  5000" in captured.out
        assert "Total Output Tokens: 3000" in captured.out
        assert "Cache Hits:       500" in captured.out
        assert "Cache Writes:     250" in captured.out
        assert "Total Tokens:        8000" in captured.out  # 5000 + 3000
        assert "Usage Metrics" in captured.out