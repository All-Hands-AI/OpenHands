import pytest
from unittest.mock import MagicMock, patch

from openhands.events.event import Event
from openhands.events.stream import EventStream
from openhands.llm.metrics import Metrics


class TestEventStream:
    def test_get_metrics_empty_stream(self):
        """Test that get_metrics returns None for an empty stream."""
        sid = "test-stream-id"
        file_store = MagicMock()
        stream = EventStream(sid=sid, file_store=file_store)
        assert stream.get_metrics() is None

    def test_get_metrics_no_metrics_in_events(self):
        """Test that get_metrics returns None when no events have metrics."""
        sid = "test-stream-id"
        file_store = MagicMock()
        stream = EventStream(sid=sid, file_store=file_store)
        event = MagicMock(spec=Event)
        event.llm_metrics = None
        
        with patch.object(stream, 'get_events', return_value=[event]):
            assert stream.get_metrics() is None

    def test_get_metrics_with_metrics(self):
        """Test that get_metrics correctly aggregates metrics from events."""
        sid = "test-stream-id"
        file_store = MagicMock()
        stream = EventStream(sid=sid, file_store=file_store)
        
        # Create mock events with metrics
        event1 = MagicMock(spec=Event)
        metrics1 = Metrics(model_name="gpt-4")
        metrics1.add_token_usage(
            prompt_tokens=10,
            completion_tokens=20,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id="resp1"
        )
        event1.llm_metrics = metrics1
        
        event2 = MagicMock(spec=Event)
        metrics2 = Metrics(model_name="gpt-4")
        metrics2.add_token_usage(
            prompt_tokens=15,
            completion_tokens=25,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id="resp2"
        )
        event2.llm_metrics = metrics2
        
        with patch.object(stream, 'get_events', return_value=[event1, event2]):
            result = stream.get_metrics()
            
            assert result is not None
            assert result.model_name == "gpt-4"
            # Check token usages are merged correctly
            total_prompt_tokens = sum(usage.prompt_tokens for usage in result.token_usages)
            total_completion_tokens = sum(usage.completion_tokens for usage in result.token_usages)
            assert total_prompt_tokens == 25  # 10 + 15
            assert total_completion_tokens == 45  # 20 + 25
            assert len(result.token_usages) == 2

    def test_get_metrics_with_exception(self):
        """Test that get_metrics handles exceptions gracefully."""
        sid = "test-stream-id"
        file_store = MagicMock()
        stream = EventStream(sid=sid, file_store=file_store)
        
        with patch.object(stream, 'get_events', side_effect=Exception("Test exception")):
            assert stream.get_metrics() is None

    def test_get_metrics_with_mixed_events(self):
        """Test that get_metrics correctly handles a mix of events with and without metrics."""
        sid = "test-stream-id"
        file_store = MagicMock()
        stream = EventStream(sid=sid, file_store=file_store)
        
        # Create mock events, some with metrics and some without
        event1 = MagicMock(spec=Event)
        metrics1 = Metrics(model_name="gpt-4")
        metrics1.add_token_usage(
            prompt_tokens=10,
            completion_tokens=20,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id="resp1"
        )
        event1.llm_metrics = metrics1
        
        event2 = MagicMock(spec=Event)
        event2.llm_metrics = None
        
        event3 = MagicMock(spec=Event)
        metrics3 = Metrics(model_name="gpt-4")
        metrics3.add_token_usage(
            prompt_tokens=15,
            completion_tokens=25,
            cache_read_tokens=0,
            cache_write_tokens=0,
            response_id="resp3"
        )
        event3.llm_metrics = metrics3
        
        with patch.object(stream, 'get_events', return_value=[event1, event2, event3]):
            result = stream.get_metrics()
            
            assert result is not None
            assert result.model_name == "gpt-4"
            # Check token usages are merged correctly
            total_prompt_tokens = sum(usage.prompt_tokens for usage in result.token_usages)
            total_completion_tokens = sum(usage.completion_tokens for usage in result.token_usages)
            assert total_prompt_tokens == 25  # 10 + 15
            assert total_completion_tokens == 45  # 20 + 25
            assert len(result.token_usages) == 2