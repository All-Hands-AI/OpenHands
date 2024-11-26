from datetime import datetime
from unittest.mock import MagicMock

from openhands.core.config.llm_config import LLMConfig
from openhands.events.event import Event, EventSource
from openhands.memory.condenser import Condenser, NoopCondenser, RecentEventsCondenser, LLMCondenser
from openhands.memory.condenser_config import (
    CondenserConfig,
    NoopCondenserConfig,
    RecentEventsCondenserConfig,
    LLMCondenserConfig,
)


def create_test_event(message: str, timestamp: datetime, source: EventSource = EventSource.USER) -> Event:
    event = Event()
    event._message = message
    event.timestamp = timestamp
    event._source = source
    return event


def test_default_condenser_config():
    """Test that the default condenser is NoopCondenser."""
    config = CondenserConfig()
    assert config.type == "noop"
    
    condenser = Condenser.from_config(config)
    assert isinstance(condenser, NoopCondenser)


def test_noop_condenser():
    events = [
        create_test_event("Event 1", datetime(2024, 1, 1, 10, 0)),
        create_test_event("Event 2", datetime(2024, 1, 1, 10, 1)),
        create_test_event("Event 3", datetime(2024, 1, 1, 10, 2))
    ]
    
    # Test direct instantiation
    condenser = NoopCondenser()
    result = condenser.condense(events)
    
    assert result == events
    assert len(result) == 3
    assert result[0]._message == "Event 1"
    assert result[2]._message == "Event 3"

    # Test from config
    config = NoopCondenserConfig(type="noop")
    condenser = Condenser.from_config(config)
    result = condenser.condense(events)
    
    assert result == events
    assert len(result) == 3


def test_recent_events_condenser():
    events = [
        create_test_event("Event 1", datetime(2024, 1, 1, 10, 0)),
        create_test_event("Event 2", datetime(2024, 1, 1, 10, 1)),
        create_test_event("Event 3", datetime(2024, 1, 1, 10, 2)),
        create_test_event("Event 4", datetime(2024, 1, 1, 10, 3)),
        create_test_event("Event 5", datetime(2024, 1, 1, 10, 4))
    ]
    
    # Test direct instantiation
    condenser = RecentEventsCondenser(max_events=2)
    result = condenser.condense(events)
    
    assert len(result) == 2
    assert result[0]._message == "Event 4"
    assert result[1]._message == "Event 5"
    
    # Test with max_events larger than list
    condenser = RecentEventsCondenser(max_events=10)
    result = condenser.condense(events)
    
    assert len(result) == 5
    assert result[0]._message == "Event 1"
    assert result[4]._message == "Event 5"

    # Test from config
    config = RecentEventsCondenserConfig(type="recent", max_events=2)
    condenser = Condenser.from_config(config)
    result = condenser.condense(events)
    
    assert len(result) == 2
    assert result[0]._message == "Event 4"
    assert result[1]._message == "Event 5"


def test_llm_condenser():
    events = [
        create_test_event("Event 1", datetime(2024, 1, 1, 10, 0)),
        create_test_event("Event 2", datetime(2024, 1, 1, 10, 1))
    ]
    
    # Test direct instantiation
    mock_llm = MagicMock()
    mock_llm.completion.return_value = {
        'choices': [{'message': {'content': 'Summary of events'}}]
    }
    
    condenser = LLMCondenser(llm=mock_llm)
    result = condenser.condense(events)
    
    assert len(result) == 1
    assert result[0]._message == "Summary of events"
    assert result[0].timestamp == events[-1].timestamp
    assert result[0].source == events[-1].source
    
    # Verify LLM was called with correct prompt
    mock_llm.completion.assert_called_once()
    call_args = mock_llm.completion.call_args[1]
    assert 'messages' in call_args
    assert len(call_args['messages']) == 1
    assert 'Event 1' in call_args['messages'][0]['content']
    assert 'Event 2' in call_args['messages'][0]['content']

    # Test from config
    llm_config = LLMConfig(model="test-model")
    config = LLMCondenserConfig(type="llm", llm_config=llm_config)
    condenser = Condenser.from_config(config)
    assert isinstance(condenser, LLMCondenser)


def test_llm_condenser_error():
    events = [create_test_event("Event 1", datetime(2024, 1, 1, 10, 0))]
    
    mock_llm = MagicMock()
    mock_llm.completion.side_effect = Exception("LLM error")
    
    condenser = LLMCondenser(llm=mock_llm)
    
    try:
        condenser.condense(events)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert str(e) == "LLM error"
