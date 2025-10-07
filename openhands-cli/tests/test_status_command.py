"""Tests for the /status command functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from openhands_cli.tui.status import display_status
from openhands.sdk.llm.utils.metrics import Metrics, TokenUsage


class TestDisplayStatus:
    """Test the display_status function."""

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_with_empty_conversation(self, mock_print_formatted, mock_print_container):
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
        
        # Call the function with a default session start time
        session_start = datetime.now()
        display_status(mock_conversation, session_start_time=session_start)
        
        # Verify that print functions were called
        assert mock_print_formatted.called
        assert mock_print_container.called
        
        # Verify conversation ID was printed
        conversation_id_call = mock_print_formatted.call_args_list[0]
        assert str(mock_conversation.id) in str(conversation_id_call)
        
        # Verify uptime was printed (should be close to 0)
        uptime_call = mock_print_formatted.call_args_list[1]
        assert "0h 0m" in str(uptime_call)

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_with_metrics(self, mock_print_formatted, mock_print_container):
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

        # Call the function with a default session start time
        session_start = datetime.now()
        display_status(mock_conversation, session_start_time=session_start)

        # Verify that print functions were called
        assert mock_print_formatted.called
        assert mock_print_container.called
        
        # Check that the container contains the expected metrics data
        container_call = mock_print_container.call_args_list[0]
        container_arg = container_call[0][0]  # First positional argument
        
        # The container should be a Frame with TextArea content
        assert hasattr(container_arg, 'body')
        text_content = container_arg.body.text
        
        # Verify metrics are displayed correctly
        assert "$0.123456" in text_content
        assert "1,500" in text_content  # Total input tokens
        assert "800" in text_content   # Total output tokens
        assert "200" in text_content   # Cache hits
        assert "100" in text_content   # Cache writes
        assert "2,300" in text_content  # Total tokens (1500 + 800)

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_with_uptime_calculation(self, mock_print_formatted, mock_print_container):
        """Test status display with uptime calculation from session start time."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Set session start time to 1 hour, 30 minutes, 45 seconds ago
        session_start = datetime.now() - timedelta(hours=1, minutes=30, seconds=45)
        
        # Call the function with session start time
        display_status(mock_conversation, session_start_time=session_start)
        
        # Verify uptime calculation
        uptime_call = mock_print_formatted.call_args_list[1]
        uptime_text = str(uptime_call)
        assert "1h 30m" in uptime_text

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_with_session_start_time(self, mock_print_formatted, mock_print_container):
        """Test status display with different session start time."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Set session start time to 5 minutes, 30 seconds ago
        session_start = datetime.now() - timedelta(minutes=5, seconds=30)
        
        # Call the function with session start time
        display_status(mock_conversation, session_start_time=session_start)
        
        # Verify uptime calculation
        uptime_call = mock_print_formatted.call_args_list[1]
        uptime_text = str(uptime_call)
        assert "5m" in uptime_text

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_zero_uptime(self, mock_print_formatted, mock_print_container):
        """Test status display with zero uptime."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function with current time as session start time (0 uptime)
        session_start = datetime.now()
        display_status(mock_conversation, session_start_time=session_start)
        
        # Verify zero uptime
        uptime_call = mock_print_formatted.call_args_list[1]
        uptime_text = str(uptime_call)
        assert "0h 0m" in uptime_text

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_with_none_token_usage(self, mock_print_formatted, mock_print_container):
        """Test status display handles None token usage gracefully."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []
        
        # Create metrics with cost but no token usage
        mock_metrics = Metrics()
        mock_metrics.accumulated_cost = 0.05
        mock_metrics.accumulated_token_usage = None
        
        # Mock conversation stats
        mock_stats = Mock()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats
        
        # Call the function with a default session start time
        session_start = datetime.now()
        display_status(mock_conversation, session_start_time=session_start)
        
        # Verify that print functions were called without error
        assert mock_print_formatted.called
        assert mock_print_container.called
        
        # Check that the container contains the expected data
        container_call = mock_print_container.call_args_list[0]
        container_arg = container_call[0][0]
        text_content = container_arg.body.text
        
        # Verify it handles None token usage gracefully
        assert "$0.050000" in text_content
        assert "0" in text_content  # Should show 0 for missing token counts

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_box_formatting(self, mock_print_formatted, mock_print_container):
        """Test that the status display creates proper formatting."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []

        # Mock conversation stats
        mock_stats = Mock()
        mock_metrics = Metrics()
        mock_stats.get_combined_metrics.return_value = mock_metrics
        mock_conversation.conversation_stats = mock_stats

        # Call the function with a default session start time
        session_start = datetime.now()
        display_status(mock_conversation, session_start_time=session_start)

        # Verify that print functions were called
        assert mock_print_formatted.called
        assert mock_print_container.called
        
        # Verify the container is a Frame (which provides the box formatting)
        container_call = mock_print_container.call_args_list[0]
        container_arg = container_call[0][0]
        
        # Should be a Frame with title "Usage Metrics"
        assert hasattr(container_arg, 'title')
        assert "Usage Metrics" in container_arg.title

    @patch('openhands_cli.tui.status.print_container')
    @patch('openhands_cli.tui.status.print_formatted_text')
    def testdisplay_status_comprehensive_scenario(self, mock_print_formatted, mock_print_container):
        """Test status display with a comprehensive scenario including all data."""
        # Create a mock conversation
        mock_conversation = Mock()
        mock_conversation.id = uuid4()
        mock_conversation.state.events = []

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

        # Set session start time to 2 hours, 15 minutes, 30 seconds ago
        session_start = datetime.now() - timedelta(hours=2, minutes=15, seconds=30)

        # Call the function with session start time
        display_status(mock_conversation, session_start_time=session_start)

        # Verify all components are present
        assert mock_print_formatted.called
        assert mock_print_container.called
        
        # Verify conversation ID
        conversation_id_call = mock_print_formatted.call_args_list[0]
        assert str(mock_conversation.id) in str(conversation_id_call)
        
        # Verify uptime
        uptime_call = mock_print_formatted.call_args_list[1]
        uptime_text = str(uptime_call)
        assert "2h 15m" in uptime_text
        
        # Verify comprehensive metrics
        container_call = mock_print_container.call_args_list[0]
        container_arg = container_call[0][0]
        text_content = container_arg.body.text
        
        assert "$1.234567" in text_content
        assert "5,000" in text_content  # Input tokens
        assert "3,000" in text_content  # Output tokens
        assert "500" in text_content   # Cache hits
        assert "250" in text_content   # Cache writes
        assert "8,000" in text_content  # Total tokens (5000 + 3000)