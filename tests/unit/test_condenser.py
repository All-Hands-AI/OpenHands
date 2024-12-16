from datetime import datetime
from unittest.mock import MagicMock

from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    LLMCondenserConfig,
    NoOpCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event, EventSource
from openhands.memory.condenser import (
    AmortizedForgettingCondenser,
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

    mock_state = MagicMock()
    mock_state.history = events

    condenser = NoOpCondenser()
    result = condenser.condense(mock_state)

    assert result == events


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

    mock_state = MagicMock()
    mock_state.history = events

    # If the max_events are larger than the number of events, equivalent to a NoOpCondenser.
    condenser = RecentEventsCondenser(max_events=len(events))
    result = condenser.condense(mock_state)

    assert result == events

    # If the max_events are smaller than the number of events, only keep the last few.
    max_events = 2
    condenser = RecentEventsCondenser(max_events=max_events)
    result = condenser.condense(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 4'
    assert result[1]._message == 'Event 5'

    # If the keep_first flag is set, the first event will always be present.
    keep_first = 1
    max_events = 2
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condense(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 5'

    # We should be able to keep more of the initial events.
    keep_first = 2
    max_events = 3
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condense(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 2'
    assert result[2]._message == 'Event 5'


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

    mock_state = MagicMock()
    mock_state.history = events
    mock_state.extra_data = {}

    mock_llm = MagicMock()

    # The LLM returns an object that we index into and treat as a pydantic model, so we have a couple of access patterns to mock.
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        'choices': [{'message': {'content': 'Summary of events'}}]
    }
    mock_response.__getitem__.return_value = [
        {'message': {'content': 'Summary of events'}}
    ]
    mock_llm.completion.return_value = mock_response
    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'test_metric': 1.0}

    condenser = LLMCondenser(llm=mock_llm)
    result = condenser.condense(mock_state)

    assert len(result) == 1
    assert result[0].content == 'Summary of events'

    # Verify LLM was called with correct prompt.
    mock_llm.completion.assert_called_once()
    call_args = mock_llm.completion.call_args[1]
    assert 'messages' in call_args
    assert len(call_args['messages']) == 1
    assert 'Event 1' in call_args['messages'][0]['content']
    assert 'Event 2' in call_args['messages'][0]['content']

    # Verify metrics were added to state
    assert 'condenser_meta' in mock_state.extra_data
    assert len(mock_state.extra_data['condenser_meta']) == 1
    assert mock_state.extra_data['condenser_meta'][0]['metrics'] == {'test_metric': 1.0}


def test_llm_condenser_error():
    """Test that LLM errors are propagated during condensation."""
    events = [create_test_event('Event 1', datetime(2024, 1, 1, 10, 0))]

    mock_state = MagicMock()
    mock_state.history = events

    mock_llm = MagicMock()
    mock_llm.completion.side_effect = Exception('LLM error')

    condenser = LLMCondenser(llm=mock_llm)

    try:
        condenser.condense(mock_state)
        raise AssertionError('Expected exception was not raised.')
    except Exception as e:
        assert str(e) == 'LLM error'


def test_amortized_forgetting_condenser_from_config():
    """Test that AmortizedForgettingCondenser objects can be made from config."""
    max_size = 50
    config = AmortizedForgettingCondenserConfig(max_size=max_size)
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, AmortizedForgettingCondenser)
    assert condenser.max_size == max_size


def test_amortized_forgetting_condenser():
    """Test that AmortizedForgettingCondenser correctly maintains and forgets history."""
    # Create a sequence of events with timestamps
    events = [
        create_test_event('Event 1', datetime(2024, 1, 1, 10, 0)),
        create_test_event('Event 2', datetime(2024, 1, 1, 10, 1)),
        create_test_event('Event 3', datetime(2024, 1, 1, 10, 2)),
    ]

    mock_state = MagicMock()
    mock_state.history = events[:2]  # Initially only first two events

    # Create condenser with small max_size to test forgetting
    condenser = AmortizedForgettingCondenser(max_size=4)

    # First call should store first two events
    result = condenser.condense(mock_state)
    assert len(result) == 2
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 2'

    # Add third event to state
    mock_state.history = events
    result = condenser.condense(mock_state)
    assert len(result) == 3
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 2'
    assert result[2]._message == 'Event 3'

    # Add same events again - should not duplicate
    result = condenser.condense(mock_state)
    assert len(result) == 3
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 2'
    assert result[2]._message == 'Event 3'

    # Add more events to trigger forgetting
    new_events = events + [
        create_test_event('Event 4', datetime(2024, 1, 1, 10, 3)),
        create_test_event('Event 5', datetime(2024, 1, 1, 10, 4)),
    ]
    mock_state.history = new_events
    result = condenser.condense(mock_state)
    assert len(result) == 3  # Should have forgotten first two events
    assert result[0]._message == 'Event 3'
    assert result[1]._message == 'Event 4'
    assert result[2]._message == 'Event 5'
