from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    LLMAttentionCondenserConfig,
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
    ObservationMaskingCondenserConfig,
    RecentEventsCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event, EventSource
from openhands.events.observation.observation import Observation
from openhands.llm import LLM
from openhands.memory.condenser import (
    AmortizedForgettingCondenser,
    Condenser,
    ImportantEventSelection,
    LLMAttentionCondenser,
    LLMSummarizingCondenser,
    NoOpCondenser,
    ObservationMaskingCondenser,
    RecentEventsCondenser,
)


def create_test_event(
    message: str, timestamp: datetime | None = None, id: int | None = None
) -> Event:
    """Create a simple test event."""
    event = Event()
    event._message = message
    event.timestamp = timestamp if timestamp else datetime.now()
    if id:
        event._id = id
    event._source = EventSource.USER
    return event


@pytest.fixture
def mock_llm() -> LLM:
    """Mocks an LLM object with a utility function for setting and resetting response contents in unit tests."""
    # Create a MagicMock for the LLM object
    mock_llm = MagicMock(
        spec=LLM,
        config=MagicMock(
            spec=LLMConfig, model='gpt-4o', api_key='test_key', custom_llm_provider=None
        ),
        metrics=MagicMock(),
    )
    _mock_content = None

    # Set a mock message with the mocked content
    mock_message = MagicMock()
    mock_message.content = _mock_content

    def set_mock_response_content(content: Any):
        """Set the mock response for the LLM."""
        nonlocal mock_message
        mock_message.content = content

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_llm.completion.return_value = mock_response

    # Attach helper methods to the mock object
    mock_llm.set_mock_response_content = set_mock_response_content

    return mock_llm


@pytest.fixture
def mock_state() -> State:
    """Mocks a State object with the only parameters needed for testing condensers: history and extra_data."""
    mock_state = MagicMock(spec=State)
    mock_state.history = []
    mock_state.extra_data = {}

    return mock_state


def test_noop_condenser_from_config():
    """Test that the NoOpCondenser objects can be made from config."""
    config = NoOpCondenserConfig()
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, NoOpCondenser)


def test_noop_condenser():
    """Test that NoOpCondensers preserve their input events."""
    events = [
        create_test_event('Event 1'),
        create_test_event('Event 2'),
        create_test_event('Event 3'),
    ]

    mock_state = MagicMock()
    mock_state.history = events

    condenser = NoOpCondenser()
    result = condenser.condensed_history(mock_state)

    assert result == events


def test_observation_masking_condenser_from_config():
    """Test that ObservationMaskingCondenser objects can be made from config."""
    attention_window = 5
    config = ObservationMaskingCondenserConfig(attention_window=attention_window)
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, ObservationMaskingCondenser)
    assert condenser.attention_window == attention_window


def test_observation_masking_condenser_respects_attention_window(mock_state):
    """Test that ObservationMaskingCondenser only masks events outside the attention window."""
    attention_window = 3
    condenser = ObservationMaskingCondenser(attention_window=attention_window)

    events = [
        create_test_event('Event 1'),
        Observation('Observation 1'),
        create_test_event('Event 3'),
        create_test_event('Event 4'),
        Observation('Observation 2'),
    ]

    mock_state.history = events
    result = condenser.condensed_history(mock_state)

    assert len(result) == len(events)

    for index, (event, condensed_event) in enumerate(zip(events, result)):
        # If we're outside the attention window, observations should be masked.
        if index < len(events) - attention_window:
            if isinstance(event, Observation):
                assert '<MASKED>' in str(condensed_event)

        # If we're within the attention window, events are unchanged.
        else:
            assert event == condensed_event


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
        create_test_event('Event 1'),
        create_test_event('Event 2'),
        create_test_event('Event 3'),
        create_test_event('Event 4'),
        create_test_event('Event 5'),
    ]

    mock_state = MagicMock()
    mock_state.history = events

    # If the max_events are larger than the number of events, equivalent to a NoOpCondenser.
    condenser = RecentEventsCondenser(max_events=len(events))
    result = condenser.condensed_history(mock_state)

    assert result == events

    # If the max_events are smaller than the number of events, only keep the last few.
    max_events = 2
    condenser = RecentEventsCondenser(max_events=max_events)
    result = condenser.condensed_history(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 4'
    assert result[1]._message == 'Event 5'

    # If the keep_first flag is set, the first event will always be present.
    keep_first = 1
    max_events = 2
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 5'

    # We should be able to keep more of the initial events.
    keep_first = 2
    max_events = 3
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(mock_state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 2'
    assert result[2]._message == 'Event 5'


def test_llm_condenser_from_config():
    """Test that LLMCondensers can be made from config."""
    config = LLMSummarizingCondenserConfig(
        llm_config=LLMConfig(
            model='gpt-4o',
            api_key='test_key',
        )
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, LLMSummarizingCondenser)
    assert condenser.llm.config.model == 'gpt-4o'
    assert condenser.llm.config.api_key == 'test_key'


def test_llm_condenser(mock_llm, mock_state):
    """Test that LLMCondensers use the LLM to generate a summary event."""
    events = [
        create_test_event('Event 1'),
        create_test_event('Event 2'),
    ]
    mock_state.history = events

    mock_llm.metrics = MagicMock()
    mock_llm.metrics.get.return_value = {'test_metric': 1.0}

    mock_llm.set_mock_response_content('Summary of events')

    condenser = LLMSummarizingCondenser(llm=mock_llm)
    result = condenser.condensed_history(mock_state)

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

    condenser = LLMSummarizingCondenser(llm=mock_llm)

    try:
        condenser.condensed_history(mock_state)
        raise AssertionError('Expected exception was not raised.')
    except Exception as e:
        assert str(e) == 'LLM error'


def test_amortized_forgetting_condenser_from_config():
    """Test that AmortizedForgettingCondenser objects can be made from config."""
    max_size = 50
    keep_first = 10
    config = AmortizedForgettingCondenserConfig(
        max_size=max_size, keep_first=keep_first
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, AmortizedForgettingCondenser)
    assert condenser.max_size == max_size
    assert condenser.keep_first == keep_first


def test_amortized_forgetting_condenser_invalid_config():
    """Test that AmortizedForgettingCondenser raises error when keep_first > max_size."""
    pytest.raises(ValueError, AmortizedForgettingCondenser, max_size=4, keep_first=2)
    pytest.raises(ValueError, AmortizedForgettingCondenser, max_size=0)
    pytest.raises(ValueError, AmortizedForgettingCondenser, keep_first=-1)


def test_amortized_forgetting_condenser_grows_to_max_size():
    """Test that AmortizedForgettingCondenser correctly maintains an event context up to max size."""
    max_size = 15
    condenser = AmortizedForgettingCondenser(max_size=max_size)

    mock_state = MagicMock()
    mock_state.extra_data = {}
    mock_state.history = []

    for i in range(max_size):
        event = create_test_event(f'Event {i}')
        mock_state.history.append(event)
        results = condenser.condensed_history(mock_state)
        assert len(results) == i + 1


def test_amortized_forgetting_condenser_forgets_when_larger_than_max_size():
    """Test that the AmortizedForgettingCondenser forgets events when the context grows too large."""
    max_size = 2
    condenser = AmortizedForgettingCondenser(max_size=max_size)

    mock_state = MagicMock()
    mock_state.extra_data = {}
    mock_state.history = []

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i}')
        mock_state.history.append(event)
        results = condenser.condensed_history(mock_state)

        # The last event in the results is always the event we just added.
        assert results[-1] == event

        # The number of results should bounce back and forth between 1, 2, 1, 2, ...
        assert len(results) == (i % 2) + 1


def test_amortized_forgetting_condenser_keeps_first_events():
    """Test that the AmortizedForgettingCondenser keeps the right number of initial events when forgetting."""
    max_size = 4
    keep_first = 1
    condenser = AmortizedForgettingCondenser(max_size=max_size, keep_first=keep_first)

    first_event = create_test_event('Event 0')

    mock_state = MagicMock()
    mock_state.extra_data = {}
    mock_state.history = [first_event]

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i+1}', datetime(2024, 1, 1, 10, i + 1))
        mock_state.history.append(event)
        results = condenser.condensed_history(mock_state)

        # The last event is always the event we just added.
        assert results[-1] == event

        # The first event is always the first event.
        assert results[0] == first_event

        # The number of results should bounce back between 2, 3, 4, 2, 3, 4, ...
        print(len(results))
        assert len(results) == (i % 3) + 2


def test_llm_attention_condenser_from_config():
    """Test that LLMAttentionCondenser objects can be made from config."""
    config = LLMAttentionCondenserConfig(
        max_size=50,
        keep_first=10,
        llm_config=LLMConfig(
            model='gpt-4o',
            api_key='test_key',
        ),
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, LLMAttentionCondenser)
    assert condenser.llm.config.model == 'gpt-4o'
    assert condenser.llm.config.api_key == 'test_key'
    assert condenser.max_size == 50
    assert condenser.keep_first == 10


def test_llm_attention_condenser_invalid_config():
    """Test that LLMAttentionCondenser raises an error if the configured LLM doesn't support response schema."""
    config = LLMAttentionCondenserConfig(
        max_size=50,
        keep_first=10,
        llm_config=LLMConfig(
            model='claude-2',  # Older model that doesn't support response schema
            api_key='test_key',
        ),
    )

    pytest.raises(ValueError, LLMAttentionCondenser.from_config, config)


def test_llm_attention_condenser_keeps_first_events(mock_llm, mock_state):
    """Test that the LLMAttentionCondenser keeps the right number of initial events when forgetting."""
    max_size = 4
    condenser = LLMAttentionCondenser(max_size=max_size, keep_first=1, llm=mock_llm)

    first_event = create_test_event('Event 0', id=0)
    mock_state.history.append(first_event)

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i+1}', id=i + 1)
        mock_state.history.append(event)

        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in mock_state.history]
            ).model_dump_json()
        )
        results = condenser.condensed_history(mock_state)

        # The first event is always the first event.
        assert results[0] == first_event


def test_llm_attention_condenser_grows_to_max_size(mock_llm, mock_state):
    """Test that LLMAttentionCondenser correctly maintains an event context up to max size."""
    max_size = 15
    condenser = LLMAttentionCondenser(max_size=max_size, llm=mock_llm)

    for i in range(max_size):
        event = create_test_event(f'Event {i}')
        mock_state.history.append(event)
        mock_llm.set_mock_response_content(
            ImportantEventSelection(ids=[event.id for event in mock_state.history])
        )
        results = condenser.condensed_history(mock_state)
        assert len(results) == i + 1


def test_llm_attention_condenser_forgets_when_larger_than_max_size(
    mock_llm, mock_state
):
    """Test that the LLMAttentionCondenser forgets events when the context grows too large."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, llm=mock_llm)

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i}', id=i)
        mock_state.history.append(event)

        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in mock_state.history]
            ).model_dump_json()
        )

        results = condenser.condensed_history(mock_state)

        # The number of results should bounce back and forth between 1, 2, 1, 2, ...
        assert len(results) == (i % 2) + 1


def test_llm_attention_condenser_handles_events_outside_history(mock_llm, mock_state):
    """Test that the LLMAttentionCondenser handles event IDs that aren't from the event history."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, llm=mock_llm)

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i}', id=i)
        mock_state.history.append(event)

        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in mock_state.history] + [-1, -2, -3, -4]
            ).model_dump_json()
        )
        results = condenser.condensed_history(mock_state)

        # The number of results should bounce back and forth between 1, 2, 1, 2, ...
        assert len(results) == (i % 2) + 1


def test_llm_attention_condenser_handles_too_many_events(mock_llm, mock_state):
    """Test that the LLMAttentionCondenser handles when the response contains too many event IDs."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, llm=mock_llm)

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i}', id=i)
        mock_state.history.append(event)
        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in mock_state.history]
                + [event.id for event in mock_state.history]
            ).model_dump_json()
        )
        results = condenser.condensed_history(mock_state)

        # The number of results should bounce back and forth between 1, 2, 1, 2, ...
        assert len(results) == (i % 2) + 1


def test_llm_attention_condenser_handles_too_few_events(mock_llm, mock_state):
    """Test that the LLMAttentionCondenser handles when the response contains too few event IDs."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, llm=mock_llm)

    for i in range(max_size * 10):
        event = create_test_event(f'Event {i}', id=i)
        mock_state.history.append(event)

        mock_llm.set_mock_response_content(
            ImportantEventSelection(ids=[]).model_dump_json()
        )

        results = condenser.condensed_history(mock_state)

        # The number of results should bounce back and forth between 1, 2, 1, 2, ...
        assert len(results) == (i % 2) + 1
