"""
Tests for the trajectory summarizer module.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from openhands.events.stream import EventStream
from openhands.memory.trajectory_summarizer.summarizer import (
    TrajectoryProcessor,
    TrajectorySummarizer,
    extract_timestamps,
    parse_llm_response_to_json,
)


class TestTrajectoryProcessor:
    """Tests for the TrajectoryProcessor class."""

    def test_preprocess_trajectory(self):
        """Test preprocessing a trajectory."""
        # Sample trajectory data
        trajectory_data = [
            {
                'action': 'message',
                'id': '1',
                'source': 'user',
                'content': 'Hello, I need help with my code.',
                'timestamp': '2023-01-01 12:00:00',
            },
            {
                'action': 'message',
                'id': '2',
                'source': 'agent',
                'content': "I'll help you with your code. What's the issue?",
                'timestamp': '2023-01-01 12:01:00',
            },
            # Item with no action - should be skipped
            {'id': '3', 'source': 'system', 'content': 'System message'},
            # Item with no content - should be skipped
            {'action': 'message', 'id': '4', 'source': 'user'},
        ]

        # Process the trajectory
        processed = TrajectoryProcessor.preprocess_trajectory(trajectory_data)

        # Check the result
        assert len(processed) == 2
        assert processed[0]['action'] == 'message'
        assert processed[0]['id'] == '1'
        assert processed[0]['source'] == 'user'
        assert processed[0]['content'] == 'Hello, I need help with my code.'
        assert processed[0]['timestamp'] == '2023-01-01 12:00:00'

    def test_format_trajectory_for_prompt(self):
        """Test formatting a trajectory for the prompt."""
        # Sample processed trajectory
        processed_trajectory = [
            {'action': 'message', 'id': '1', 'source': 'user', 'content': 'Hello'}
        ]

        # Format the trajectory
        formatted = TrajectoryProcessor.format_trajectory_for_prompt(
            processed_trajectory
        )

        # Check the result
        assert isinstance(formatted, str)
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert len(parsed) == 1
        assert parsed[0]['action'] == 'message'


class TestTimestampExtraction:
    """Tests for timestamp extraction functions."""

    def test_extract_timestamps(self):
        """Test extracting timestamps from a range string."""
        # Test valid timestamp range
        start, end = extract_timestamps('12:00:00-12:30:00')
        assert start == '12:00:00'
        assert end == '12:30:00'

        # Test shorter format
        start, end = extract_timestamps('12:00-12:30')
        assert start == '12:00'
        assert end == '12:30'

        # Test invalid format
        start, end = extract_timestamps('12:00:00')
        assert start is None
        assert end is None

        # Test None input
        start, end = extract_timestamps(None)
        assert start is None
        assert end is None


class TestResponseParsing:
    """Tests for LLM response parsing."""

    def test_parse_llm_response_to_json(self):
        """Test parsing an LLM response to JSON."""
        # Test valid JSON response with ids
        response = """```json
{
  "overall_summary": "User asked for help with code",
  "segments": [
    {
      "timestamp_range": "12:00:00-12:30:00",
      "title": "Initial request",
      "summary": "User asked for help",
      "ids": [1, 2, 3]
    }
  ]
}
```"""

        parsed = parse_llm_response_to_json(response)

        assert parsed['overall_summary'] == 'User asked for help with code'
        assert len(parsed['segments']) == 1
        assert parsed['segments'][0]['title'] == 'Initial request'
        assert parsed['segments'][0]['start_timestamp'] == '12:00:00'
        assert parsed['segments'][0]['end_timestamp'] == '12:30:00'
        assert parsed['segments'][0]['ids'] == [1, 2, 3]

        # Test valid JSON response without ids
        response = """```json
{
  "overall_summary": "User asked for help with code",
  "segments": [
    {
      "timestamp_range": "12:00:00-12:30:00",
      "title": "Initial request",
      "summary": "User asked for help"
    }
  ]
}
```"""

        parsed = parse_llm_response_to_json(response)

        assert parsed['overall_summary'] == 'User asked for help with code'
        assert len(parsed['segments']) == 1
        assert parsed['segments'][0]['title'] == 'Initial request'
        assert parsed['segments'][0]['start_timestamp'] == '12:00:00'
        assert parsed['segments'][0]['end_timestamp'] == '12:30:00'
        assert 'ids' in parsed['segments'][0]
        assert parsed['segments'][0]['ids'] == []

        # Test invalid JSON response
        response = 'This is not JSON'
        parsed = parse_llm_response_to_json(response)

        assert parsed['overall_summary'] == 'Failed to parse response'
        assert len(parsed['segments']) == 0


@pytest.mark.parametrize(
    'llm_provided',
    [
        True,
        False,
    ],
)
class TestTrajectorySummarizer:
    """Tests for the TrajectorySummarizer class."""

    def test_init(self, llm_provided):
        """Test initializing the summarizer."""
        mock_llm = MagicMock() if llm_provided else None
        mock_llm_config = MagicMock() if not llm_provided else None

        summarizer = TrajectorySummarizer(
            llm=mock_llm,
            llm_config=mock_llm_config,
            temperature=0.0,
        )

        # Check that the LLM and config were set correctly
        assert summarizer.llm == mock_llm
        assert summarizer.llm_config == mock_llm_config
        assert summarizer.temperature == 0.0

    def test_summarize_trajectory(self, llm_provided):
        """Test summarizing a trajectory."""
        # Mock the LLM
        mock_llm = MagicMock()

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """```json
{
  "overall_summary": "Test summary",
  "segments": []
}
```"""
        mock_llm.completion.return_value = mock_response

        # Initialize the summarizer with the mock LLM
        summarizer = TrajectorySummarizer(
            llm=mock_llm if llm_provided else None,
            llm_config=MagicMock() if not llm_provided else None,
            temperature=0.0,
        )

        # If LLM is not provided, we need to mock the LLM class
        if not llm_provided:
            with patch(
                'openhands.memory.trajectory_summarizer.summarizer.LLM',
                return_value=mock_llm,
            ):
                # Summarize a trajectory
                trajectory = [{'action': 'message', 'content': 'Hello'}]
                summary = summarizer.summarize_trajectory(trajectory)
        else:
            # Summarize a trajectory
            trajectory = [{'action': 'message', 'content': 'Hello'}]
            summary = summarizer.summarize_trajectory(trajectory)

        # Check that the LLM was called with the right parameters
        mock_llm.completion.assert_called_once()
        call_args = mock_llm.completion.call_args[1]
        assert call_args['temperature'] == 0.0
        assert len(call_args['messages']) == 1

        # Check the summary
        assert summary['overall_summary'] == 'Test summary'
        assert len(summary['segments']) == 0

    def test_batch_summarize_trajectories(self, llm_provided):
        """Test batch summarizing trajectories."""
        # Mock the LLM
        mock_llm = MagicMock()

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """```json
{
  "overall_summary": "Test summary",
  "segments": []
}
```"""
        mock_llm.completion.return_value = mock_response

        # Initialize the summarizer
        summarizer = TrajectorySummarizer(
            llm=mock_llm if llm_provided else None,
            llm_config=MagicMock() if not llm_provided else None,
            temperature=0.0,
        )

        # Batch summarize trajectories
        trajectories = [
            [{'action': 'message', 'content': 'Hello'}],
            [{'action': 'message', 'content': 'World'}],
        ]

        # If LLM is not provided, we need to mock the LLM class
        if not llm_provided:
            with patch(
                'openhands.memory.trajectory_summarizer.summarizer.LLM',
                return_value=mock_llm,
            ):
                summaries = summarizer.batch_summarize_trajectories(trajectories)
        else:
            summaries = summarizer.batch_summarize_trajectories(trajectories)

        # Check that the LLM was called twice
        assert mock_llm.completion.call_count == 2

        # Check the summaries
        assert len(summaries) == 2
        assert summaries[0]['overall_summary'] == 'Test summary'
        assert summaries[1]['overall_summary'] == 'Test summary'

    @pytest.mark.asyncio
    async def test_summarize_conversation(self, llm_provided):
        """Test summarizing a conversation."""
        # Mock the LLM
        mock_llm = MagicMock()

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """```json
{
  "overall_summary": "Test summary",
  "segments": []
}
```"""
        mock_llm.completion.return_value = mock_response

        # Mock the event stream
        mock_event_stream = MagicMock(spec=EventStream)

        # Mock the get_trajectory_from_event_stream method
        trajectory = [{'action': 'message', 'content': 'Hello'}]

        # Initialize the summarizer
        summarizer = TrajectorySummarizer(
            llm=mock_llm if llm_provided else None,
            llm_config=MagicMock() if not llm_provided else None,
            temperature=0.0,
        )

        # Mock the get_trajectory_from_event_stream method
        with patch.object(
            TrajectorySummarizer,
            'get_trajectory_from_event_stream',
            return_value=trajectory,
        ):
            # If LLM is not provided, we need to mock the LLM class
            if not llm_provided:
                with patch(
                    'openhands.memory.trajectory_summarizer.summarizer.LLM',
                    return_value=mock_llm,
                ):
                    summary = await summarizer.summarize_conversation(mock_event_stream)
            else:
                summary = await summarizer.summarize_conversation(mock_event_stream)

        # Check the summary
        assert summary['overall_summary'] == 'Test summary'
        assert len(summary['segments']) == 0
