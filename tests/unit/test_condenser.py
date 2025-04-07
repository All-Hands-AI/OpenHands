from datetime import datetime
from typing import Any, Callable, Iterable
from unittest.mock import MagicMock

import pytest

from openhands.controller.state.state import State
from openhands.core.config.condenser_config import (
    AmortizedForgettingCondenserConfig,
    BrowserOutputCondenserConfig,
    LLMAttentionCondenserConfig,
    LLMSummarizingCondenserConfig,
    NoOpCondenserConfig,
    ObservationMaskingCondenserConfig,
    RecentEventsCondenserConfig,
    StructuredSummaryCondenserConfig,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.message import Message, TextContent
from openhands.events.event import Event, EventSource
from openhands.events.observation import BrowserOutputObservation
from openhands.events.observation.agent import AgentCondensationObservation
from openhands.events.observation.observation import Observation
from openhands.llm import LLM
from openhands.memory.condenser import Condenser
from openhands.memory.condenser.condenser import Condensation, RollingCondenser, View
from openhands.memory.condenser.impl import (
    AmortizedForgettingCondenser,
    BrowserOutputCondenser,
    ImportantEventSelection,
    LLMAttentionCondenser,
    LLMSummarizingCondenser,
    NoOpCondenser,
    ObservationMaskingCondenser,
    RecentEventsCondenser,
    StructuredSummaryCondenser,
)


def create_test_event(
    message: str, timestamp: datetime | None = None, id: int | None = None
) -> Event:
    """Create a simple test event."""
    event = Event()
    event._message = message
    event.timestamp = timestamp if timestamp else datetime.now()
    if id is not None:
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

    mock_llm.format_messages_for_llm = lambda events: [
        Message(role='user', content=[TextContent(text=str(event))]) for event in events
    ]

    mock_llm.is_function_calling_active.return_value = True

    return mock_llm


class RollingCondenserTestHarness:
    """Test harness for rolling condensers.

    Simulates the behavior of a simple agent loop (appropriately handling the distinction between `View` and `Condensation` results) and provides utilities for testing the results.
    """

    def __init__(self, condenser: RollingCondenser):
        self.condenser = condenser
        self.callbacks: list[Callable[[list[Event]], None]] = []

    def add_callback(self, callback: Callable[[list[Event]], None]):
        """Add a callback to the test harness.

        This callback will be called on the history after each event is added, but before the condenser is applied. You can use this to export information about the event that was just added, or to set LLM responses based on the state.
        """
        self.callbacks.append(callback)

    def views(self, events: Iterable[Event]) -> Iterable[View]:
        """Generate a sequence of views similating the condenser's behavior over the given event stream.

        This generator assumes we're starting from an empty history.
        """
        state = State()

        for event in events:
            state.history.append(event)
            for callback in self.callbacks:
                callback(state.history)

            match self.condenser.condensed_history(state):
                case View() as view:
                    yield view

                case Condensation(event=condensation_event):
                    state.history.append(condensation_event)

    def expected_size(self, index: int, max_size: int) -> int:
        """Calculate the expected size of the view at the given index.

        Assumes the condenser triggers condensation when the view is _longer_ than the max size, and that the target size is half the max size.
        """
        # Until we hit the max size, the views should grow monotonically.
        if index < max_size:
            return index + 1

        # Once we hit the max size, the next view should be reduced to the target size.
        target_size = max_size // 2

        # So when the index is the same as the max size, we should have target size + 1 events in the view.
        # And the maximum value we will ever see is the max size (approximately 2 * target size).
        # Put together, we get the following formula:
        return ((index - max_size) % target_size) + target_size + 1

    def expected_condensations(self, index: int, max_size: int) -> int:
        """Calculate the expected number of condensation events at the given index.

        Assumes the condenser triggers condensation when the view is _longer_ than the max size, and that the target size is half the max size.
        """
        if index < max_size:
            return 0

        target_size = max_size // 2
        return ((index - max_size) // target_size) + 1


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
    state = State()
    state.history = events

    condenser = NoOpCondenser()
    result = condenser.condensed_history(state)

    assert result == View(events=events)


def test_observation_masking_condenser_from_config():
    """Test that ObservationMaskingCondenser objects can be made from config."""
    attention_window = 5
    config = ObservationMaskingCondenserConfig(attention_window=attention_window)
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, ObservationMaskingCondenser)
    assert condenser.attention_window == attention_window


def test_observation_masking_condenser_respects_attention_window():
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

    state = State()
    state.history = events
    result = condenser.condensed_history(state)

    assert len(result) == len(events)

    for index, (event, condensed_event) in enumerate(zip(events, result)):
        # If we're outside the attention window, observations should be masked.
        if index < len(events) - attention_window:
            if isinstance(event, Observation):
                assert '<MASKED>' in str(condensed_event)

        # If we're within the attention window, events are unchanged.
        else:
            assert event == condensed_event


def test_browser_output_condenser_from_config():
    """Test that BrowserOutputCondenser objects can be made from config."""
    attention_window = 5
    config = BrowserOutputCondenserConfig(attention_window=attention_window)
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, BrowserOutputCondenser)
    assert condenser.attention_window == attention_window


def test_browser_output_condenser_respects_attention_window():
    """Test that BrowserOutputCondenser only masks events outside the attention window."""
    attention_window = 3
    condenser = BrowserOutputCondenser(attention_window=attention_window)

    events = [
        BrowserOutputObservation('Observation 1', url='', trigger_by_action=''),
        BrowserOutputObservation('Observation 2', url='', trigger_by_action=''),
        create_test_event('Event 3'),
        create_test_event('Event 4'),
        BrowserOutputObservation('Observation 3', url='', trigger_by_action=''),
        BrowserOutputObservation('Observation 4', url='', trigger_by_action=''),
    ]

    state = State()
    state.history = events

    result = condenser.condensed_history(state)

    assert len(result) == len(events)
    cnt = 4
    for event, condensed_event in zip(events, result):
        if isinstance(event, BrowserOutputObservation):
            if cnt > attention_window:
                assert 'Content Omitted' in str(condensed_event)
            else:
                assert event == condensed_event
            cnt -= 1
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

    state = State()
    state.history = events

    # If the max_events are larger than the number of events, equivalent to a NoOpCondenser.
    condenser = RecentEventsCondenser(max_events=len(events))
    result = condenser.condensed_history(state)

    assert result == View(events=events)

    # If the max_events are smaller than the number of events, only keep the last few.
    max_events = 3
    condenser = RecentEventsCondenser(max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'  # kept from keep_first
    assert result[1]._message == 'Event 4'  # kept from max_events
    assert result[2]._message == 'Event 5'  # kept from max_events

    # If the keep_first flag is set, the first event will always be present.
    keep_first = 1
    max_events = 2
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 5'

    # We should be able to keep more of the initial events.
    keep_first = 2
    max_events = 3
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'  # kept from keep_first
    assert result[1]._message == 'Event 2'  # kept from keep_first
    assert result[2]._message == 'Event 5'  # kept from max_events


def test_llm_summarizing_condenser_from_config():
    """Test that LLMSummarizingCondenser objects can be made from config."""
    config = LLMSummarizingCondenserConfig(
        max_size=50,
        keep_first=10,
        llm_config=LLMConfig(
            model='gpt-4o',
            api_key='test_key',
        ),
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, LLMSummarizingCondenser)
    assert condenser.llm.config.model == 'gpt-4o'
    assert condenser.llm.config.api_key.get_secret_value() == 'test_key'
    assert condenser.max_size == 50
    assert condenser.keep_first == 10


def test_llm_summarizing_condenser_invalid_config():
    """Test that LLMSummarizingCondenser raises error when keep_first > max_size."""
    pytest.raises(
        ValueError,
        LLMSummarizingCondenser,
        llm=MagicMock(),
        max_size=4,
        keep_first=2,
    )
    pytest.raises(ValueError, LLMSummarizingCondenser, llm=MagicMock(), max_size=0)
    pytest.raises(ValueError, LLMSummarizingCondenser, llm=MagicMock(), keep_first=-1)


def test_llm_summarizing_condenser_gives_expected_view_size(mock_llm):
    """Test that LLMSummarizingCondenser maintains the correct view size."""
    max_size = 10
    condenser = LLMSummarizingCondenser(max_size=max_size, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    # Set up mock LLM response
    mock_llm.set_mock_response_content('Summary of forgotten events')

    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_llm_summarizing_condenser_keeps_first_and_summary_events(mock_llm):
    """Test that the LLM summarizing condenser appropriately maintains the event prefix and any summary events."""
    max_size = 10
    keep_first = 3
    condenser = LLMSummarizingCondenser(
        max_size=max_size, keep_first=keep_first, llm=mock_llm
    )

    mock_llm.set_mock_response_content('Summary of forgotten events')

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]
    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)

        # Ensure that the we've called out the summarizing LLM once per condensation
        assert mock_llm.completion.call_count == harness.expected_condensations(
            i, max_size
        )

        # Ensure that the prefix is appropiately maintained
        assert view[:keep_first] == events[: min(keep_first, i + 1)]

        # If we've condensed, ensure that the summary event is present
        if i > max_size:
            assert isinstance(view[keep_first], AgentCondensationObservation)


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


def test_amortized_forgetting_condenser_gives_expected_view_size():
    """Test that AmortizedForgettingCondenser maintains a context view of the correct size."""
    max_size = 12
    condenser = AmortizedForgettingCondenser(max_size=max_size)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_amortized_forgetting_condenser_keeps_first_and_last_events():
    """Test that the AmortizedForgettingCondenser keeps the prefix and suffix events, even when condensing."""
    max_size = 12
    keep_first = 4
    condenser = AmortizedForgettingCondenser(max_size=max_size, keep_first=keep_first)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    # To ensure the most recent event is always recorded, track it in a non-local variable udpated
    # with a closure we'll pass to the view generator as a callback.
    most_recent_event: Event | None = None

    def set_most_recent_event(history: list[Event]):
        nonlocal most_recent_event
        most_recent_event = history[-1]

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_most_recent_event)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)

        # The last event should always be the most-recently added.
        assert view[-1] == most_recent_event

        # The prefix should always match the list of events, up to the keep_first limit.
        assert view[:keep_first] == events[: min(keep_first, i + 1)]


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
    assert condenser.llm.config.api_key.get_secret_value() == 'test_key'
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


def test_llm_attention_condenser_gives_expected_view_size(mock_llm):
    """Test that the LLMAttentionCondenser gives views of the expected size."""
    max_size = 10
    condenser = LLMAttentionCondenser(max_size=max_size, keep_first=0, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    def set_response_content(history: list[Event]):
        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in history]
            ).model_dump_json()
        )

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_response_content)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_llm_attention_condenser_handles_events_outside_history(mock_llm):
    """Test that the LLMAttentionCondenser handles event IDs that aren't from the event history."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, keep_first=0, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    def set_response_content(history: list[Event]):
        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in history] + [-1, -2, -3, -4]
            ).model_dump_json()
        )

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_response_content)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_llm_attention_condenser_handles_too_many_events(mock_llm):
    """Test that the LLMAttentionCondenser handles when the response contains too many event IDs."""
    max_size = 2
    condenser = LLMAttentionCondenser(max_size=max_size, keep_first=0, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    def set_response_content(history: list[Event]):
        mock_llm.set_mock_response_content(
            ImportantEventSelection(
                ids=[event.id for event in history] + [event.id for event in history]
            ).model_dump_json()
        )

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_response_content)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_llm_attention_condenser_handles_too_few_events(mock_llm):
    """Test that the LLMAttentionCondenser handles when the response contains too few event IDs."""
    max_size = 2
    # Developer note: We must specify keep_first=0 because
    # keep_first (1) >= max_size//2 (1) is invalid.
    condenser = LLMAttentionCondenser(max_size=max_size, keep_first=0, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    def set_response_content(history: list[Event]):
        mock_llm.set_mock_response_content(
            ImportantEventSelection(ids=[]).model_dump_json()
        )

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_response_content)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_llm_attention_condenser_handles_keep_first_events(mock_llm):
    """Test that LLMAttentionCondenser works when keep_first=1 is allowed (must be less than half of max_size)."""
    max_size = 12
    keep_first = 4
    condenser = LLMAttentionCondenser(
        max_size=max_size, keep_first=keep_first, llm=mock_llm
    )

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    def set_response_content(history: list[Event]):
        mock_llm.set_mock_response_content(
            ImportantEventSelection(ids=[]).model_dump_json()
        )

    harness = RollingCondenserTestHarness(condenser)
    harness.add_callback(set_response_content)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)
        assert view[:keep_first] == events[: min(keep_first, i + 1)]


def test_structured_summary_condenser_from_config():
    """Test that StructuredSummaryCondenser objects can be made from config."""
    config = StructuredSummaryCondenserConfig(
        max_size=50,
        keep_first=10,
        llm_config=LLMConfig(
            model='gpt-4o',
            api_key='test_key',
        ),
    )
    condenser = Condenser.from_config(config)

    assert isinstance(condenser, StructuredSummaryCondenser)
    assert condenser.llm.config.model == 'gpt-4o'
    assert condenser.llm.config.api_key.get_secret_value() == 'test_key'
    assert condenser.max_size == 50
    assert condenser.keep_first == 10


def test_structured_summary_condenser_invalid_config():
    """Test that StructuredSummaryCondenser raises error when keep_first > max_size."""
    # Since the condenser only works when function calling is on, we need to
    # mock up the check for that.
    llm = MagicMock()
    llm.is_function_calling_active.return_value = True

    pytest.raises(
        ValueError,
        StructuredSummaryCondenser,
        llm=llm,
        max_size=4,
        keep_first=2,
    )

    pytest.raises(ValueError, StructuredSummaryCondenser, llm=llm, max_size=0)
    pytest.raises(ValueError, StructuredSummaryCondenser, llm=llm, keep_first=-1)

    # If all other parameters are good but there's no function calling the
    # condenser still counts as improperly configured.
    llm.is_function_calling_active.return_value = False
    pytest.raises(
        ValueError, StructuredSummaryCondenser, llm=llm, max_size=40, keep_first=2
    )


def test_structured_summary_condenser_gives_expected_view_size(mock_llm):
    """Test that StructuredSummaryCondenser maintains the correct view size."""
    max_size = 10
    condenser = StructuredSummaryCondenser(max_size=max_size, llm=mock_llm)

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]

    # Set up mock LLM response
    mock_llm.set_mock_response_content('Summary of forgotten events')

    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)


def test_structured_summary_condenser_keeps_first_and_summary_events(mock_llm):
    """Test that the StructuredSummaryCondenser appropriately maintains the event prefix and any summary events."""
    max_size = 10
    keep_first = 3
    condenser = StructuredSummaryCondenser(
        max_size=max_size, keep_first=keep_first, llm=mock_llm
    )

    mock_llm.set_mock_response_content('Summary of forgotten events')

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]
    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)

        # Ensure that the we've called out the summarizing LLM once per condensation
        assert mock_llm.completion.call_count == harness.expected_condensations(
            i, max_size
        )

        # Ensure that the prefix is appropiately maintained
        assert view[:keep_first] == events[: min(keep_first, i + 1)]

        # If we've condensed, ensure that the summary event is present
        if i > max_size:
            assert isinstance(view[keep_first], AgentCondensationObservation)
