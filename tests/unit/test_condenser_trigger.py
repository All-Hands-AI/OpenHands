from unittest.mock import MagicMock

from openhands.controller.agent import LLMCompletionProvider
from openhands.controller.state.state import State
from openhands.events.action.message import MessageAction
from openhands.events.event import Event, EventSource
from openhands.llm.llm import LLM
from openhands.memory.condenser.trigger import (
    ConversationTokenTrigger,
    EventCountTrigger,
    KeywordTrigger,
    OrTrigger,
)
from openhands.memory.view import View


def msg(message: str):
    event = MessageAction(message)
    event._source = EventSource.USER  # type: ignore
    return event


def test_event_count_trigger():
    max_events = 5
    trigger = EventCountTrigger(max_events=max_events)

    events: list[Event] = [msg(f'Event {i}') for i in range(max_events)]
    view = View(events=events)
    state = State()

    # Should not trigger condensation
    assert not trigger.should_condense(view, state)

    # Add one more event to exceed the limit
    events.append(msg('Event 6'))
    view = View(events=events)

    # Should trigger condensation
    assert trigger.should_condense(view, state)


def test_keyword_trigger():
    trigger_word = 'condense'
    trigger = KeywordTrigger(trigger_word=trigger_word)

    events: list[Event] = [
        msg('Hello'),
        msg(f'Please {trigger_word} this conversation'),
    ]
    view = View(events=events)
    state = State()

    # Should trigger condensation
    assert trigger.should_condense(view, state)

    # Change the last user message to not contain the trigger word
    events[-1] = msg('Please summarize this conversation')
    view = View(events=events)

    # Should not trigger condensation
    assert not trigger.should_condense(view, state)


def test_conversation_token_trigger():
    max_tokens = 100
    trigger = ConversationTokenTrigger(max_tokens=max_tokens)

    mock_agent = MagicMock(spec=LLMCompletionProvider)
    mock_agent.llm = MagicMock(spec=LLM)
    mock_agent.llm.get_token_count.return_value = 50

    events: list[Event] = [msg('Event 1'), msg('Event 2')]
    view = View(events=events)
    state = State()

    # Should not trigger condensation
    assert not trigger.should_condense(view, state, mock_agent)

    # Exceed the token limit
    mock_agent.llm.get_token_count.return_value = 150

    # Should trigger condensation
    assert trigger.should_condense(view, state, mock_agent)


def test_or_trigger():
    trigger1 = EventCountTrigger(max_events=5)
    trigger2 = KeywordTrigger(trigger_word='condense')
    or_trigger = OrTrigger(trigger1, trigger2)

    events: list[Event] = [msg('Event 1'), msg('Event 2')]
    view = View(events=events)
    state = State()

    # Neither trigger should activate
    assert not or_trigger.should_condense(view, state)

    # Exceed the event count limit
    events.extend([msg(f'Event {i}') for i in range(3, 7)])
    view = View(events=events)

    # Should trigger condensation due to event count
    assert or_trigger.should_condense(view, state)

    # Reset events and test keyword trigger
    events = [
        msg('Hello'),
        msg('Please condense this conversation'),
    ]
    view = View(events=events)

    # Should trigger condensation due to keyword
    assert or_trigger.should_condense(view, state)
