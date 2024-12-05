from datetime import datetime
from unittest.mock import MagicMock

from openhands.core.config.condenser_config import (
    LLMCondenserConfig,
    NoOpCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event, EventSource
from openhands.memory.condenser import (
    Condenser,
    LLMCondenser,
    NoOpCondenser,
    RecentEventsCondenser,
)


def create_test_event(
    message: str, timestamp: datetime, source: EventSource = EventSource.USER
) -> Event:
    event = Event()
    event._message = message
    event.timestamp = timestamp
    event._source = source
    return event


def test_noop_condenser_from_config():
    """Test that the NoOpCondenser objects can be made from config."""
    config = NoOpCondenserConfig()
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, NoOpCondenser)


def test_noop_condenser():
    """Test that NoOpCondensers preserve their input events."""
    events = [
        create_test_event('Event 1', datetime(2024, 1, 1, 10, 0)),
        create_test_event('Event 2', datetime(2024, 1, 1, 10, 1)),
        create_test_event('Event 3', datetime(2024, 1, 1, 10, 2)),
    ]

    condenser = NoOpCondenser()
    result = condenser.condense(events)

    assert result.condensed_events == events


def test_recent_events_condenser_from_config():
    """Test that RecentEventsCondenser objects can be made from config."""
    max_events = 5
    keep_first = True
    config = RecentEventsCondenserConfig(keep_first=keep_first, max_events=max_events)
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, RecentEventsCondenser)
    assert condenser.max_events == max_events
    assert condenser.keep_first == keep_first


def test_recent_events_condenser():
    """Test that RecentEventsCondensers keep just the most recent events."""
    events = [
        create_test_event('Event 1', datetime(2024, 1, 1, 10, 0)),
        create_test_event('Event 2', datetime(2024, 1, 1, 10, 1)),
        create_test_event('Event 3', datetime(2024, 1, 1, 10, 2)),
        create_test_event('Event 4', datetime(2024, 1, 1, 10, 3)),
        create_test_event('Event 5', datetime(2024, 1, 1, 10, 4)),
    ]

    # If the max_events are larger than the number of events, equivalent to a NoOpCondenser.
    condenser = RecentEventsCondenser(max_events=len(events) + 1)
    result = condenser.condense(events)

    assert result.condensed_events == events

    # If the max_events are smaller than the number of events, only keep the last few.
    max_events = 2
    condenser = RecentEventsCondenser(max_events=max_events)
    result = condenser.condense(events)

    assert len(result.condensed_events) == max_events
    assert result.condensed_events[0]._message == 'Event 4'
    assert result.condensed_events[1]._message == 'Event 5'

    # If the keep_first flag is set, the first event will always be present.
    keep_first = True
    max_events = 1
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condense(events)

    assert len(result.condensed_events) == max_events + 1
    assert result.condensed_events[0]._message == 'Event 1'
    assert result.condensed_events[1]._message == 'Event 5'


def test_llm_condenser_from_config():
    """Test that LLMCondensers can be made from config."""
    config = LLMCondenserConfig(
        llm_config=LLMConfig(
            model='gpt-4o',
            api_key='test_key',
        )
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, LLMCondenser)
    assert condenser.llm.config.model == 'gpt-4o'
    assert condenser.llm.config.api_key == 'test_key'


def test_llm_condenser():
    """Test that LLMCondensers use the LLM to generate a summary event."""
    events = [
        create_test_event('Event 1', datetime(2024, 1, 1, 10, 0)),
        create_test_event('Event 2', datetime(2024, 1, 1, 10, 1)),
    ]

    mock_llm = MagicMock()
    mock_llm.completion.return_value = {
        'choices': [{'message': {'content': 'Summary of events'}}]
    }

    condenser = LLMCondenser(llm=mock_llm)
    result = condenser.condense(events)

    assert len(result.condensed_events) == 1
    assert result.condensed_events[0].content == 'Summary of events'

    # Verify LLM was called with correct prompt.
    mock_llm.completion.assert_called_once()
    call_args = mock_llm.completion.call_args[1]
    assert 'messages' in call_args
    assert len(call_args['messages']) == 1
    assert 'Event 1' in call_args['messages'][0]['content']
    assert 'Event 2' in call_args['messages'][0]['content']


def test_llm_condenser_error():
    """Test that LLM errors are propagated during condensation."""
    events = [create_test_event('Event 1', datetime(2024, 1, 1, 10, 0))]

    mock_llm = MagicMock()
    mock_llm.completion.side_effect = Exception('LLM error')

    condenser = LLMCondenser(llm=mock_llm)

    try:
        condenser.condense(events)
        raise AssertionError('Expected exception was not raised.')
    except Exception as e:
        assert str(e) == 'LLM error'
